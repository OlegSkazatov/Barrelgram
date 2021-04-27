import sys

import requests
import threading
import time
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QStackedWidget

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
        self.main = Main()
        self.stack.addWidget(self.main)
        self.stack.setGeometry(self.geometry())
        self.stack.show()
        self.requestThread = RequestThread()
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
    def __init__(self):
        super().__init__()
        self.initUI()
        self.dialogues = {}
        self.active_dialogue = None
        self.delta_down = 0

    def initUI(self):
        uic.loadUi('ui/main.ui', self)
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
        self.messages.hide()
        self.message_input.hide()
        self.current_user.hide()
        self.button_file.hide()
        self.button_block.hide()
        self.button_log_out.clicked.connect(self.logOut)

        for b in self.dialogue_buttons.buttons():
            b.clicked.connect(self.openDialogue)

    def updateData(self, jsonfile, load_photo=False):
        my_id = jsonfile["id"]
        self.dialogues = jsonfile["dialogues"]
        if self.dialogues["amount"] < 10:  # Скрываем пустые яйчейки диалогов
            for i in range(1, 11):
                if i > self.dialogues["amount"]:
                    for el in self.uiDialogues[i - 1]:
                        el.hide()

        for i in range(10):
            name = self.dialogues[str(i + 1)]["name"]
            last_message = self.dialogues[str(i + 1)]["last_message"]
            new_messages = self.dialogues[str(i + 1)]["new_messages"]
            new = self.dialogues[str(i + 1)]["new"]
            last_message_time = self.dialogues[str(i + 1)]["last_message_time"]

            self.uiDialogues[i][1].setText(name)
            self.uiDialogues[i][2].setText(last_message)
            if new or load_photo:
                pass
                # Здесь должна быть загрузка аватарок
            self.uiDialogues[i][4].setText(str(new_messages))
            if new_messages == 0:
                self.uiDialogues[i][4].hide()
            self.uiDialogues[i][5].setText(last_message_time)

        self.your_id.setText("Your id: " + str(my_id))

    def keyPressEvent(self, event):
        if int(event.modifiers()) == Qt.CTRL:
            if event.key() == Qt.Key_Return and self.message_input.toPlainText().replace(" ", "").replace("\t",
                                                                                                          "") != "":
                self.send_message(self.message_input.toPlainText())

    def send_message(self, message):
        id_1 = self.active_dialogue
        data = {
            "action": "text",
            "message": message,
            "receiver": self.dialogues[str(self.delta_down + self.active_dialogue)]["photo"]
        }

        requests.post("http://" + SERVER_ADDRESS +
                      f"/main/dialogue/{self.dialogues[str(self.delta_down + id_1)]['id']}", data=data)
        self.message_input.setPlainText("")

    def updateActiveDialogue(self):
        if self.active_dialogue is None:
            return
        id_1 = self.active_dialogue
        msgs = requests.get("http://" + SERVER_ADDRESS +
                            f"/main/dialogue/{self.dialogues[str(self.delta_down + id_1)]['id']}").json()
        my_id = int(self.your_id.text().split(" ")[2])
        text = ""
        for key in msgs.keys():
            msg = msgs[key]
            show = ""
            if msg["user"] == my_id:
                show += "You: "
            else:
                show += f"{self.uiDialogues[id_1 - 1][1].text().split(' ')[0]}: "
            show += msg["text"]
            text = text + "\n" + show
        self.messages.setText(text)

    def openDialogue(self):
        id = int(self.sender().objectName().split("_")[1])
        if id == self.active_dialogue:
            return
        self.messages.show()
        self.message_input.show()
        self.current_user.show()
        self.button_file.show()
        self.button_block.show()
        self.messages.setText("")

        self.active_dialogue = id
        msgs = requests.get("http://" + SERVER_ADDRESS +
                            f"/main/dialogue/{self.dialogues[str(self.delta_down + id)]['id']}").json()

        my_id = int(self.your_id.text().split(" ")[2])
        for key in msgs.keys():
            msg = msgs[key]
            show = ""
            if msg["user"] == my_id:
                show += "You: "
            else:
                show += f"{self.uiDialogues[id - 1][1].text().split(' ')[0]}: "
            show += msg["text"]
            self.messages.setText(self.messages.text() + "\n" + show)

    def logOut(self):
        global SEND_GET_REQUESTS
        requests.get("http://" + SERVER_ADDRESS + "/go_out")
        SEND_GET_REQUESTS = False
        main.stack.setCurrentWidget(main)


class RequestThread(QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        while True:
            if SEND_GET_REQUESTS:
                response = requests.get("http://" + SERVER_ADDRESS + "/main/dialogues").json()
                main.stack.currentWidget().updateData(response, load_photo=False)
                main.stack.currentWidget().updateActiveDialogue()
            time.sleep(1)


# get_handler = threading.Thread(  # Запуск параллельного потока
#     target=cikle,
#     args=(),
#     daemon=True
# )
# get_handler.start()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Login()  # Создаём и отображаем главное окно
    main.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
