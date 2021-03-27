from sqlalchemy import Integer, Text, Boolean, MetaData, Column


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
