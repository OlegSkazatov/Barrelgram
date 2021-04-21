import sys

import requests
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow

SERVER_ADDRESS = "127.0.0.1:9999"


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi('ui/login.ui', self)
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


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()  # Создаём и отображаем главное окно
    main.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
