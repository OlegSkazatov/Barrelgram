from sqlalchemy import create_engine, Table
import os


class Database:
    def __init__(self, fname):
        if not os.path.join(fname):
            raise FileNotFoundError("Указанный файл не найден!")
        self.engine = create_engine("sqlite:///{}".format(fname))

    def connection(self):
        return self.engine.connect()

    def createTable(self, name, meta, *columns):
        table = Table(name, meta, *columns)
        table.create(self.engine, checkfirst=True)

    def dropTable(self, name):
        self.execute("DROP TABLE {}".format(name))

    def execute(self, sql):
        con = self.connection()
        return con.execute(sql)
