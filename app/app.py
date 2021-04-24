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
        self.stack.setGeometry(self.geometry())
        self.stack.show()
        self.button_login.clicked.connect(self.login)

    def login(self):
        if self.login_input.text() == "" or self.password_input.text() == "":
            return

        params = {
            "app_client": True,
            "login": self.login_input.text(),
            "password": self.password_input.text()
        }

        response = requests.get("http://" + SERVER_ADDRESS, params=params).json()
        if response["verdict"] == "denied":
            self.button_login.setText("Ты даун")


class Main(QWidget):
    def __init__(self, jsonfile):
        super().__init__()
        uic.loadUi('ui/main.ui', self)
        self.initUI(jsonfile)

    def initUI(self, jsonfile):
        my_id = jsonfile["id"]
        self.your_id.setText("Your id: " + str(my_id))




def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Login()  # Создаём и отображаем главное окно
    main.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
