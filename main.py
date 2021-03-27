import os
import sqlite3

from flask import Flask, render_template, request, redirect

from email_authorize.EmailManager import EmailManager
from Database.Database import Database
from Database.table_init import table_init

emailManager = EmailManager()

conn = sqlite3.connect('database.db', check_same_thread=False)  # Создание файла базы данных, если его нет
sql = conn.cursor()
conn.commit()
conn.close()

database = Database("database.db")  # Создаём объект для работы с БД
table_init(database)  # Создаём главные таблицы если их нет

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.route('/', methods=['POST', 'GET'])
def menu():
    ip = request.remote_addr
    result = database.execute(f"SELECT email FROM users WHERE ip = '{ip}'")
    if result.first() is not None:
        return redirect("/main")
    if request.method == 'GET':
        return render_template('menu.html', problem=0)
    else:
        result = database.execute(f"SELECT email FROM users WHERE email = '{request.form['email']}'")
        try:
            emails = result.first()[0]
        except IndexError:
            emails = []
        if request.form['email'] not in emails:
            return render_template('menu.html', problem=1)
        else:
            result = database.execute(f"SELECT password FROM users WHERE email = '{request.form['email']}'")
            password = result.first()[0]
            if password == request.form['password']:
                database.execute(
                    f"UPDATE users SET ip = '{str(ip)}' WHERE email = '{request.form['email']}'")
                return redirect("/settings")
            else:
                return render_template('menu.html', problem=1)


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
        # result = database.execute(f"SELECT ip FROM users WHERE ip = '{ip}'")
        # if sql.fetchone() is not None:
        #     return render_template('reg.html',
        #                            messenge='Вы можете зарегестрировать только 1 аккаунт!')
        if request.form['password'] != request.form['password2']:
            return render_template("reg.html", messenge='Пароли не совпадают')
        elif len(request.form['password']) < 8:
            return render_template("reg.html", messenge='Слишком короткий пароль!')
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
    return "Владимир Путин Молодец, а это в разработке"


if __name__ == '__main__':
    app.run(port=9999, host='127.0.0.1')
