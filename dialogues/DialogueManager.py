from sqlalchemy import Integer, Text, Boolean, MetaData, Column, Time


class DialogueManager:
    def __init__(self, database):
        self.database = database

    def createNew(self, id1, id2):
        self.database.execute(f"INSERT INTO dialogues ('{str(id1)};{str(id2)}'), '', 0")
        id = self.database.execute(f"SELECT id FROM dialogues WHERE users = '{str(id1)};{str(id2)}'").first()[0]

        meta = MetaData()
        self.database.createTable(f'dial_{id}', meta, Column("id", Integer, primary_key=True, autoincrement=True),
                                  Column("user", Integer),
                                  Column("time", Time),
                                  Column("type", Text),
                                  Column("message", Text))

    def sendMessage(self, dial_id, user_id, message):
        pass

    def sendVideo(self, dial_id, user_id, path):
        pass

    def sendPhoto(self, dial_id, user_id, path):
        pass

    def sendAudio(self, dial_id, user_id, path):
        pass
