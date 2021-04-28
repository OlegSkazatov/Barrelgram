from sqlalchemy import Integer, Text, Boolean, MetaData, Column, Time


def table_init(database):
    meta = MetaData()
    # Таблица users хранит лицчные данные пользователей. Столбец ip показывает, выполнен ли вход с какого-либо ip
    database.createTable("users", meta, Column("id", Integer, primary_key=True, autoincrement=True),
                         Column("email", Text),
                         Column("ip", Text),
                         Column("password", Text),
                         Column("confirmed", Boolean),
                         Column("name", Text),
                         Column("birthday", Text),
                         Column("sex", Text))
    # Тут хранятся id диалогов, участники и информация о последнем сообщении.
    # Колонка blocked не понадобилась, но она есть
    database.createTable("dialogues", meta, Column("id", Integer, primary_key=True, autoincrement=True),
                         Column("users", Text),
                         Column("last_message", Text),
                         Column("last_message_time", Text),
                         Column("blocked", Boolean))
