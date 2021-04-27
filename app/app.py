import sys
import os

import requests
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import QPixmap
import time
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QStackedWidget, QFileDialog

SERVER_ADDRESS = "127.0.0.1:9999"
SEND_GET_REQUESTS = False


class Login(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi('ui/login.ui', self)
        self.stack = QStackedWidget()
        self.stack.addWidget(self)
        self.stack.setCurrentWidget(self)
        self.requestThread = RequestThread()
        self.main = Main(self.requestThread)
        self.stack.addWidget(self.main)
        self.stack.setGeometry(self.geometry())
        self.stack.show()
        self.requestThread.start()
        self.button_login.clicked.connect(self.login)

    #        self.login(raw=True) Тут цыганские фокусы у PyQt, хз пока как пофиксить

    def login(self, raw=False):
        if (self.login_input.text() == "" or self.password_input.text() == "") and not raw:
            return

        params = {
            "app_client": True,
            "login": self.login_input.text(),
            "password": self.password_input.text()
        }

        response = requests.get("http://" + SERVER_ADDRESS, params=params).json()
        if response["verdict"] == "denied":
            if not raw:
                self.button_login.setText("Ты даун")
            return
        else:
            if not raw:
                global SEND_GET_REQUESTS
                self.main.updateData(response, load_photo=True)
                self.stack.setCurrentWidget(self.main)
                SEND_GET_REQUESTS = True


class Main(QWidget):
    def __init__(self, requestThread):
        super().__init__()
        self.dialogues = {}
        self.active_dialogue = None
        self.delta_down = 0
        self.searching = False
        self.requestThread = requestThread
        self.buttonThread = ButtonThread()
        self.buttonThread.start()
        self.buttonThread.triggered.connect(self.light_active_dialogue)
        self.initUI()
        self.dial_text = ""

    def initUI(self):
        uic.loadUi('ui/main.ui', self)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.uiMessages = [self.line_1, self.line_2, self.line_3, self.line_4, self.line_5,
                           self.line_6, self.line_7, self.line_8, self.line_9, self.line_10,
                           self.line_11, self.line_12, self.line_13, self.line_14, self.line_15, self.line_16]
        # Здесь хранятся ссылки на ui объекты кнопок с диалогами, чтобы их было удобнее доставать потом
        self.uiDialogues = (
            (self.dial_1, self.name_1, self.last_message_1, self.photo_1, self.new_messages_1, self.time_1),
            (self.dial_2, self.name_2, self.last_message_2, self.photo_2, self.new_messages_2, self.time_2),
            (self.dial_3, self.name_3, self.last_message_3, self.photo_3, self.new_messages_3, self.time_3),
            (self.dial_4, self.name_4, self.last_message_4, self.photo_4, self.new_messages_4, self.time_4),
            (self.dial_5, self.name_5, self.last_message_5, self.photo_5, self.new_messages_5, self.time_5),
            (self.dial_6, self.name_6, self.last_message_6, self.photo_6, self.new_messages_6, self.time_6),
            (self.dial_7, self.name_7, self.last_message_7, self.photo_7, self.new_messages_7, self.time_7),
            (self.dial_8, self.name_8, self.last_message_8, self.photo_8, self.new_messages_8, self.time_8),
            (self.dial_9, self.name_9, self.last_message_9, self.photo_9, self.new_messages_9, self.time_9),
            (self.dial_10, self.name_10, self.last_message_10, self.photo_10, self.new_messages_10, self.time_10))
        self.my_i = None  # Все экземпляры ImageQt и QPixmap должны, судя по всему, храниться в памяти
        self.my_pixmap = None  # Иначе картинки начинают творить что-то страшное
        # Поэтому в эти аттрибуты записываются все ImageQt и QPixmap
        self.pixmaps = [['' for i in range(10)], ['' for i in range(10)]]
        self.message_input.hide()
        self.button_file.hide()
        self.button_log_out.clicked.connect(self.logOut)
        self.button_support.clicked.connect(self.support)
        self.search.editingFinished.connect(self.search_fun)
        self.button_file.clicked.connect(self.send_file)
        self.requestThread.response_got.connect(self.handleResponse)

        for b in self.dialogue_buttons.buttons():
            b.clicked.connect(self.openDialogue)

    def handleResponse(self, jsonfile):
        self.updateData(jsonfile, load_photo=False)
        self.updateActiveDialogue()

    def light_active_dialogue(self):
        if self.active_dialogue is None:
            for el in self.uiDialogues:
                el[0].setStyleSheet("border-top: 2px solid #DCDCDC;background-color: rgba(255, 147, 85, 0);")
        else:
            self.uiDialogues[self.active_dialogue - 1][0]\
                .setStyleSheet("border-top: 2px solid #DCDCDC;background-color: rgba(255, 147, 85, 120);")

    def support(self):
        self.search.setText("1")
        self.search_fun()

    def updateData(self, jsonfile, load_photo=False):
        my_id = jsonfile["id"]
        my_name = jsonfile["name"]
        if load_photo:
            self.my_i = self.load_photo(my_id, self.current_user_photo)
            self.my_pixmap = QPixmap.fromImage(self.my_i)
            self.current_user_photo.setPixmap(self.my_pixmap)
        self.dialogues = jsonfile["dialogues"]
        if self.dialogues["amount"] < 10:  # Скрываем пустые яйчейки диалогов
            for i in range(1, 11):
                if i > self.dialogues["amount"]:
                    for el in self.uiDialogues[i - 1]:
                        el.hide()
                else:
                    for el in self.uiDialogues[i - 1]:
                        el.show()
        for i in range(10):
            name = self.dialogues[str(i + 1)]["name"]
            last_message = self.dialogues[str(i + 1)]["last_message"]
            new_messages = self.dialogues[str(i + 1)]["new_messages"]
            new = self.dialogues[str(i + 1)]["new"]
            if name != "":
                last_message_time = self.dialogues[str(i + 1)]["last_message_time"]
            else:
                last_message_time = ""

            self.uiDialogues[i][1].setText(name)
            self.uiDialogues[i][2].setText(last_message)
            if new or load_photo:
                self.pixmaps[0][i] = self.load_photo(jsonfile["dialogues"][str(i + 1)]["photo"], self.uiDialogues[i][3])
                self.pixmaps[1][i] = QPixmap.fromImage(self.pixmaps[0][i])
                if name != "":
                    self.uiDialogues[i][3].setPixmap(self.pixmaps[1][i])
            if name == "":
                self.uiDialogues[i][3].clear()
            self.uiDialogues[i][4].setText(str(new_messages))
            if new_messages == 0:
                self.uiDialogues[i][4].hide()
            self.uiDialogues[i][5].setText(last_message_time)

        self.your_id.setText("Your id: " + str(my_id))
        self.current_user.setText(my_name)

    def search_fun(self):
        if "🔎" in self.search.text() or self.search.text() == "":
            self.search.setText("🔎 Enter name or id")
        else:
            global SEND_GET_REQUESTS
            SEND_GET_REQUESTS = False
            self.searching = True
            self.active_dialogue = None
            for el in self.uiMessages:
                el.clear()
            params = {
                "txt": self.search.text()
            }
            users = requests.get("http://" + SERVER_ADDRESS + "/main/search", params=params).json()
            self.updateData(users, load_photo=True)

    def send_file(self):
        if self.active_dialogue is None:
            return
        fname = QFileDialog.getOpenFileName(self, 'Choose a file', '',
                                            'Image (*.jpg);;Image (*.png);;'
                                            ' Image (*.bmp);;Audio (*.mp3);;Video (*.mp4)')[0]
        if os.path.exists(fname):
            size = os.stat(fname).st_size / (1024 * 1024)
            if size > 200:
                return False
            type = fname.split(".")[-1]
            action = None
            if type in ["jpg", "png", "bmp"]:
                action = "photo"
            elif type == "mp3":
                action = "audio"
            elif type == "mp4":
                action = "video"
            if action is None:
                return False

            file = open(fname, "rb")
            data = {
                "action": action,
                "receiver": self.dialogues[str(self.delta_down + self.active_dialogue)]["photo"]
            }
            files = {
                "file": file
            }

            requests.post(
                "http://" + SERVER_ADDRESS + f"/main/dialogue/{self.dialogues[str(self.active_dialogue)]['id']}",
                data=data, files=files, stream=True)

    def keyPressEvent(self, event):
        if int(event.modifiers()) == Qt.CTRL:
            if event.key() == Qt.Key_Return and self.message_input.toPlainText().replace(" ", "").replace("\t",
                                                                                                          "") != "":
                self.send_message(self.message_input.toPlainText())

    def wheelEvent(self, event):
        if self.active_dialogue is None:
            return

        if event.angleDelta().y() > 0:
            if self.delta_down < len(self.dial_text) - 16:
                self.delta_down += 1
        elif event.angleDelta().y() < 0:
            if self.delta_down > 0:
                self.delta_down -= 1

    def send_message(self, message):
        if self.active_dialogue is None:
            return
        id_1 = self.active_dialogue
        data = {
            "action": "text",
            "message": message,
            "receiver": self.dialogues[str(self.delta_down + self.active_dialogue)]["photo"]
        }

        requests.post("http://" + SERVER_ADDRESS +
                      f"/main/dialogue/{self.dialogues[str(self.delta_down + id_1)]['id']}", data=data)
        self.message_input.setPlainText("")
        self.active_dialogue = 1
        self.updateAvatars()

    def updateActiveDialogue(self):
        if self.active_dialogue is None:
            return
        msgs = requests.get("http://" + SERVER_ADDRESS +
                            f"/main/dialogue/{self.dialogues[str(self.active_dialogue)]['id']}").json()
        my_id = int(self.your_id.text().split(" ")[2])
        text = ""
        for key in msgs.keys():
            msg = msgs[key]
            show = ""
            if msg["user"] == my_id:
                show += "You: "
            else:
                show += f"{self.uiDialogues[self.active_dialogue - 1][1].text().split(' ')[0]}: "
            if msg['type'] == "text":
                show += msg["text"]
            elif msg['type'] == "video":
                show += f"<a href=\"http://{SERVER_ADDRESS}/main/dialogue/{self.dialogues[str(self.active_dialogue)]['id']}/video/{msg['text']}\">Video</a>"
            elif msg['type'] == "photo":
                show += f"<a href=\"http://{SERVER_ADDRESS}/main/dialogue/{self.dialogues[str(self.active_dialogue)]['id']}/photo/{msg['text']}\">Photo</a>"
            elif msg['type'] == "audio":
                show += f"<a href=\"http://{SERVER_ADDRESS}/main/dialogue/{self.dialogues[str(self.active_dialogue)]['id']}/audio/{msg['text']}\">Audio</a>"
            text = text + "\n" + show
        self.setMessages(text)

    def openDialogue(self):
        global SEND_GET_REQUESTS
        id = int(self.sender().objectName().split("_")[1])
        if id == self.active_dialogue or self.uiDialogues[self.delta_down + id - 1][1].text() == "":
            return
        self.search.setText("🔎 Enter name or id")
        self.message_input.show()
        self.button_file.show()

        self.active_dialogue = id
        params = {
            "receiver": int(self.dialogues[str(id)]["photo"])
        }
        msgs = requests.get("http://" + SERVER_ADDRESS +
                            f"/main/dialogue/{self.dialogues[str(self.active_dialogue)]['id']}", params=params).json()
        if self.searching:
            self.searching = False
            self.active_dialogue = None
            SEND_GET_REQUESTS = True
        my_id = int(self.your_id.text().split(" ")[2])
        # Отображение сообщений
        text = ""
        for key in msgs.keys():
            msg = msgs[key]
            show = ""
            if msg["user"] == my_id:
                show += "You: "
            else:
                show += f"{self.uiDialogues[id - 1][1].text().split(' ')[0]}: "
            show += msg["text"]
            text = text + "\n" + show
        self.setMessages(text, scroll_to_end=True)
        self.updateAvatars()

    def setMessages(self, text, scroll_to_end=False):
        text = text.strip("\n")
        text = text.split("\n")
        text = list(map(lambda x: [x[i:i + 60] if "<a href" not in x else x for i in range(0, len(x), 60)], text))
        text = list(map(lambda x: "\n".join(x), text))
        true_text = []
        for el in text:
            if "\n" not in el:
                true_text.append(el)
            else:
                for e in el.split("\n"):
                    true_text.append(e)

        if scroll_to_end:
            self.delta_down = len(true_text) - 16
            if self.delta_down < 0:
                self.delta_down = 0
        for i in range(16):
            try:
                self.uiMessages[i].setText(true_text[self.delta_down + i])
            except IndexError:
                break
        self.dial_text = true_text

    def updateAvatars(self):
        for i in range(10):
            name = self.dialogues[str(i + 1)]["name"]
            self.pixmaps[0][i] = self.load_photo(self.dialogues[str(i + 1)]["photo"], self.uiDialogues[i][3])
            self.pixmaps[1][i] = QPixmap.fromImage(self.pixmaps[0][i])
            if name != "":
                self.uiDialogues[i][3].setPixmap(self.pixmaps[1][i])
            else:
                self.uiDialogues[i][3].clear()

    def logOut(self):
        global SEND_GET_REQUESTS
        requests.get("http://" + SERVER_ADDRESS + "/go_out")
        SEND_GET_REQUESTS = False
        main.stack.setCurrentWidget(main)

    def load_photo(self, id, label):
        if id == "":
            id = "icon"
        im = Image.open(requests.get("http://" + SERVER_ADDRESS + f"/all_avatars/{id}", stream=True).raw)
        x, y = label.geometry().width(), label.geometry().height()
        im = im.resize((x, y))
        return ImageQt(im.copy())


class RequestThread(QThread):  # Поток, делающий get запрос к серверу каждые полсекунды для обновления диалогов
    response_got = QtCore.pyqtSignal(dict)

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        while True:
            if SEND_GET_REQUESTS:
                response = requests.get("http://" + SERVER_ADDRESS + "/main/dialogues").json()
                self.response_got.emit(response)
            time.sleep(0.5)


class ButtonThread(QThread):  # Поток, подсвечивающий отдельный диалог. Было лень делать по другому

    triggered = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        while True:
            self.triggered.emit()
            time.sleep(0.01)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Login()  # Создаём и отображаем главное окно
    main.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
