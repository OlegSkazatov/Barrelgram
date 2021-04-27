import os
import sqlite3
import random
import json

from flask import Flask, render_template, request, redirect

from email_authorize.EmailManager import EmailManager
from dialogues.DialogueManager import DialogueManager
from Database.Database import Database
from Database.table_init import table_init

emailManager = EmailManager()  # Обработчик отправки сообщений для подтверждения e-mail

conn = sqlite3.connect('database.db', check_same_thread=False)  # Создание файла базы данных, если его нет
sql = conn.cursor()
conn.commit()
conn.close()

database = Database("database.db")  # Создаём объект для работы с БД
dialManager = DialogueManager(database)  # Обработчик диалогов
table_init(database)  # Создаём главные таблицы если их нет

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['TEMPLATES_AUTO_RELOAD'] = True


def login_user(username, password, ip, request, app_client):
    result = database.execute(f"SELECT email FROM users WHERE ip = '{ip}'")
    if result.first() is not None:  # Проверка, если уже выполнен вход с этого ip
        return redirect(f"/main?app_client={app_client}")
    else:
        result = database.execute(f"SELECT email FROM users WHERE email = '{username}'")
        try:
            emails = result.first()[0]
        except Exception:
            emails = []
        if username not in emails:
            if not app_client:
                return render_template('menu.html', problem=1)
            else:
                with open('responses/access_denied.json', encoding='utf-8') as response:
                    t = json.load(response)
                    t["reason"] = 1
                    return json.dumps(t)
        else:
            result = database.execute(f"SELECT password FROM users WHERE email = '{username}'")
            password_true = result.first()[0]
            if password_true == password:
                database.execute(
                    f"UPDATE users SET ip = '{str(ip)}' WHERE email = '{username}'")
                result = database.execute(f"SELECT name FROM users WHERE email = '{username}'")
                if not result.first()[0]:
                    return redirect("/settings")
                return redirect(f"/main?app_client={app_client}")
            else:
                if app_client:
                    with open('responses/access_denied.json', encoding='utf-8') as response:
                        t = json.load(response)
                        t["reason"] = 1
                        return json.dumps(t)
                return render_template('menu.html', problem=1)


def check_login(address):
    result = database.execute(f"SELECT email FROM users WHERE ip = '{address}'")
    return bool(result.first())


def getUserInfo(id):
    result = database.execute(f"SELECT * FROM users WHERE id = {str(id)}")
    return result.first()


@app.route('/', methods=['POST', 'GET'])
def menu():
    app_client = request.args.get('app_client', False) == "True"  # Проверка заходит клиент с приложения или сайта
    if not app_client:
        result = database.execute(f"SELECT email FROM users WHERE ip = '{request.remote_addr}'")
        if result.first() is not None:  # Проверка, если уже выполнен вход с этого ip
            return redirect("/main")
        if request.method == 'GET' and not app_client:
            return render_template('menu.html', problem=0)
        else:
            return login_user(request.form['email'], request.form['password'], request.remote_addr, request, False)
    else:
        login = request.args.get('login', '')
        password = request.args.get('password', '')
        return login_user(login, password, request.remote_addr, request, True)


@app.route('/reg', methods=['POST', 'GET'])
def reg():
    ip = request.remote_addr
    result = database.execute(f"SELECT email FROM users WHERE ip = '{ip}'")
    if result.first() is not None:
        return redirect("/main")
    if request.method == 'GET':
        return render_template("reg.html", password=0)
    else:
        result = database.execute(f"SELECT email FROM users WHERE email = '{request.form['email']}'")
        if result.first() is not None:
            return render_template('reg.html', messenge='Такой e-mail уже зарегестрирован')
        if request.form['password'] != request.form['password2']:
            return render_template("reg.html", messenge='Пароли не совпадают')
        elif len(request.form['password']) < 8:
            return render_template("reg.html", messenge='Слишком короткий пароль!')
        password = str(random.randint(0, 10)) + str(random.randint(0, 10)) + str(random.randint(0, 10)) + request.form[
            'password']
        database.execute(
            "INSERT INTO users (email, ip, password, confirmed, name, birthday, sex) VALUES ('{}', '{}', '{}', {}, '{}', '{}', '{}')".format(
                str(request.form['email']), '',
                str(request.form['password']), 'false',
                '', '', ''))
        return redirect(f"/email_accept/{request.form['email']}")


@app.route('/email_accept/<email>', methods=['POST', 'GET'])
def email(email):
    if request.method == 'GET':
        return render_template("pochta.html", email=email, method=request.method)
    else:
        emailManager.send_letter(email)
        return render_template("pochta.html", email=email, method=request.method)


@app.route('/email_confirm/<emaill>/<kod>')
def email_confirm(emaill, kod):
    if kod + ';' + emaill in emailManager.register_users:
        emailManager.register_users.pop(emailManager.register_users.index(kod + ';' + emaill))
        database.execute(
            f"UPDATE users SET confirmed = true WHERE email = '{emaill}'")
        return render_template("pochta.html", email=emaill, method='accept')
    else:
        return "Ссылка не верна!"


@app.route('/settings', methods=['POST', 'GET'])
def settings():
    if not check_login(request.remote_addr):
        return redirect("/")
    app_client = request.args.get('app_client', False) == "True"
    if app_client:
        with open("responses/access_denied.json", encoding="utf-8") as jsonfile:
            return jsonfile
    ip = request.remote_addr
    if request.method == 'GET':
        return render_template('settings.html')
    else:
        result = database.execute(f"SELECT email FROM users WHERE ip = '{ip}'")
        user_email = result.first()[0]
        database.execute(
            f"UPDATE users SET name = '{request.form['name'] + ';' + request.form['surname']}' WHERE email = '{user_email}'")
        database.execute(
            f"UPDATE users SET birthday = '{request.form['day'] + ';' + request.form['month'] + ';' + request.form['year']}' WHERE email = '{user_email}'")
        database.execute(
            f"UPDATE users SET sex = '{request.form['sex']}' WHERE email = '{user_email}'")
        return redirect('/main')


@app.route('/main')
def main():
    if not check_login(request.remote_addr):
        return redirect("/")
    app_client = request.args.get('app_client', False) == "True"  # Проверка заходит клиент с приложения или сайта
    if not app_client:
        return render_template('main.html',
                               ava_name='https://get.pxhere.com/photo/landscape-nature-wilderness-walking-mountain-sky-lake-adventure-view-river-valley-mountain-range-environment-rural-reflection-scenic-peaceful-glacier-scenery-serene-fjord-tourism-national-park-ridge-ecology-clouds-mountains-alps-backpacking-plateau-fell-cirque-loch-crater-lake-moraine-landform-tarn-mountain-pass-geographical-feature-mountainous-landforms-glacial-landform-848203.jpg')
    with open('responses/main_page.json', encoding='utf-8') as res:
        dct = json.load(res)
        id = int(database.execute(f"SELECT id FROM users WHERE ip = '{request.remote_addr}'").first()[0])
        dct["id"] = id
        dialogues = [el for el in database.execute(
            f"SELECT * FROM dialogues WHERE users LIKE '%{id}%' ORDER BY date(last_message_time) DESC").fetchall()]
        print(dialogues)
        dct["dialogues"]["amount"] = len(dialogues)
        for i in range(len(dialogues)):
            users = dialogues[i][1].split(";")
            users.remove(str(id))
            user = getUserInfo(int(users[0]))

            id1 = dialogues[i][0]
            name = " ".join(user[5].split(";"))
            last_message = dialogues[i][2]
            photo = int(users[0])
            result = [el for el in
                      database.execute(f"SELECT * FROM dial_{id1} WHERE new = 1 AND user != {id}").fetchall()]
            new_messages = len(result)
            result = [el for el in database.execute(f"SELECT * FROM dial_{id1}").fetchall()]
            new = len(result) == new_messages
            last_message_time = ":".join(dialManager.getMessages(id1, amount=1)[0][2].split(" ")[1].split(":")[:2])
            result.clear()

            dct["dialogues"][str(i + 1)]["id"] = id1
            dct["dialogues"][str(i + 1)]["new_messages"] = new_messages
            dct["dialogues"][str(i + 1)]["new"] = new
            dct["dialogues"][str(i + 1)]["name"] = name
            dct["dialogues"][str(i + 1)]["last_message"] = last_message
            dct["dialogues"][str(i + 1)]["last_message_time"] = last_message_time
            dct["dialogues"][str(i + 1)]["photo"] = photo
        response = json.dumps(dct)
        return response


@app.route('/main/dialogue/<id>', methods=['POST', 'GET'])
def dialogue(id):
    if not check_login(request.remote_addr):
        return redirect("/")
    if request.method == 'GET':
        user_id = database.execute(f"SELECT id FROM users WHERE ip = '{request.remote_addr}'").first()[0]
        database.execute(f"UPDATE dial_{id} SET new = 0 WHERE user != {user_id}")
        messages = dialManager.getMessages(id, 20)
        response = {}
        for message in messages:
            id = message[0]
            user = message[1]
            time = message[2]
            type = message[3]
            text = message[4]
            new = message[5]
            response[id] = {
                "user": user,
                "time": time,
                "type": type,
                "text": text,
                "new": new
            }
        return json.dumps(response)
    else:
        action = request.form['action']
        if action == "text":
            message = request.form['message'].strip("\n").replace("'", "''")
            user_id = database.execute(f"SELECT id FROM users WHERE ip = '{request.remote_addr}'").first()[0]
            receiver_id = request.form['receiver']
            dialManager.sendMessage(id, user_id, receiver_id, message)
            return "Message sent!"



@app.route("/main/dialogues")
def dialogues():
    if not check_login(request.remote_addr):
        return redirect("/")
    with open('responses/main_page.json', encoding='utf-8') as res:
        dct = json.load(res)
        id = int(database.execute(f"SELECT id FROM users WHERE ip = '{request.remote_addr}'").first()[0])
        dct["id"] = id
        dialogues = [el for el in database.execute(
            f"SELECT * FROM dialogues WHERE users LIKE '%{id}%' ORDER BY date(last_message_time) DESC").fetchall()]
        dct["dialogues"]["amount"] = len(dialogues)
        for i in range(len(dialogues)):
            users = dialogues[i][1].split(";")
            users.remove(str(id))
            user = getUserInfo(int(users[0]))

            id1 = dialogues[i][0]
            name = " ".join(user[5].split(";"))
            last_message = dialogues[i][2]
            photo = int(users[0])
            result = [el for el in database.execute(f"SELECT * FROM dial_{id1} WHERE new = 1 AND user != {id}").fetchall()]
            new_messages = len(result)
            result = [el for el in database.execute(f"SELECT * FROM dial_{id1}").fetchall()]
            new = len(result) == new_messages
            last_message_time = ":".join(dialManager.getMessages(id1, amount=1)[0][2].split(" ")[1].split(":")[:2])
            result.clear()

            dct["dialogues"][str(i + 1)]["id"] = id1
            dct["dialogues"][str(i + 1)]["new_messages"] = new_messages
            dct["dialogues"][str(i + 1)]["new"] = new
            dct["dialogues"][str(i + 1)]["name"] = name
            dct["dialogues"][str(i + 1)]["last_message"] = last_message
            dct["dialogues"][str(i + 1)]["last_message_time"] = last_message_time
            dct["dialogues"][str(i + 1)]["photo"] = photo
        response = json.dumps(dct)
        return response


@app.route('/go_out')
def go_out():
    ip = request.remote_addr
    database.execute(
        f"UPDATE users SET ip = '' WHERE ip = '{ip}'")
    return redirect('/')


if __name__ == '__main__':
    app.run(port=9999, host='127.0.0.1')
