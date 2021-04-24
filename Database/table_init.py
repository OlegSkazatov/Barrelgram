from sqlalchemy import Integer, Text, Boolean, MetaData, Column, Time


def table_init(database):
    meta = MetaData()
    database.createTable("users", meta, Column("id", Integer, primary_key=True, autoincrement=True),
                         Column("email", Text),
                         Column("ip", Text),
                         Column("password", Text),
                         Column("confirmed", Boolean),
                         Column("name", Text),
                         Column("birthday", Text),
                         Column("sex", Text))
    database.createTable("dialogues", meta, Column("id", Integer, primary_key=True, autoincrement=True),
                         Column("users", Text),
                         Column("last_message", Text),
                         Column("last_message_time", Text),
                         Column("blocked", Boolean))
