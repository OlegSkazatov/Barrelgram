import sys

import requests
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QStackedWidget

SERVER_ADDRESS = "127.0.0.1:9999"


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
                self.main.updateData(response)
                self.stack.setCurrentWidget(self.main)


class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.dialogues = {}
        self.active_dialogue = None

    def initUI(self):
        uic.loadUi('ui/main.ui', self)
        self.uiDialogues = [[self.dial_1, self.name_1, self.last_message_1, self.photo_1],
                            [self.dial_2, self.name_2, self.last_message_2, self.photo_2],
                            [self.dial_3, self.name_3, self.last_message_3, self.photo_3],
                            [self.dial_4, self.name_4, self.last_message_4, self.photo_4],
                            [self.dial_5, self.name_5, self.last_message_5, self.photo_5],
                            [self.dial_6, self.name_6, self.last_message_6, self.photo_6],
                            [self.dial_7, self.name_7, self.last_message_7, self.photo_7],
                            [self.dial_8, self.name_8, self.last_message_8, self.photo_8],
                            [self.dial_9, self.name_9, self.last_message_9, self.photo_9],
                            [self.dial_10, self.name_10, self.last_message_10, self.photo_10]]
        self.messages.hide()
        self.message_input.hide()
        self.current_user.hide()
        self.button_file.hide()
        self.button_block.hide()

        for b in self.dialogue_buttons.buttons():
            b.clicked.connect(self.openDialogue)

    def updateData(self, jsonfile):
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

            self.uiDialogues[i][1].setText(name)
            self.uiDialogues[i][2].setText(last_message)

        self.your_id.setText("Your id: " + str(my_id))

    def openDialogue(self):
        id = int(self.sender().objectName().split("_")[1])


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Login()  # Создаём и отображаем главное окно
    main.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
