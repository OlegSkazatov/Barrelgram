import random
import smtplib
import json


class EmailManager:
    def __init__(self):
        jsonfile = open("email_authorize/email_login.json", "r")  # Получаем логин и пароль от нашей почты из файла
        data = json.load(jsonfile)
        my_email = data["login"]
        password = data["password"]
        jsonfile.close()

        self.register_users = []  # Создаём объект SMTP и выполняем вход
        self.my_email = my_email
        self.smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
        self.smtpObj.starttls()
        self.smtpObj.login(my_email, password)

    def send_letter(self, email):  # Отправка сообщения, почта передаётся как аргумент
        kod = str(random.randint(10000, 99999))  # Сложные алгоритмы генерации кода
        self.register_users.append(kod + ';' + email)
        message = "\r\n".join([
            "From: %s" % self.my_email,
            "To: %s" % email,
            "Subject: Confirm your email",
            "",
            str(f"http://olay-messenger.xyz:25936/email_confirm/{email}/{kod}")  # Такое письмо по любому попадёт в спам
        ])
        self.smtpObj.sendmail(self.my_email, [email], message)
