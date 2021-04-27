from sqlalchemy import Integer, Text, Boolean, MetaData, Column, Time


class DialogueManager:
    def __init__(self, database):
        self.database = database

    def createNew(self, id1, id2):
        self.database.execute(f"INSERT INTO dialogues (users, last_message, last_message_time, blocked)"
                              f" VALUES('{str(id1)};{str(id2)}', '', datetime('now', 'localtime'), 0)")
        id = self.database.execute(f"SELECT id FROM dialogues WHERE users = '{str(id1)};{str(id2)}'").first()[0]
        self.database.execute(f"CREATE TABLE if not exists dial_{id} (id INTEGER PRIMARY KEY AUTOINCREMENT, user INTEGER,"
                              " time TEXT, type TEXT, message TEXT, new BOOLEAN)")


    def getMessages(self, dial_id, amount=-1):
        result = self.database.execute(f"SELECT * FROM dial_{dial_id}").fetchall()
        if amount == -1 or amount > len(result):
            return result
        return result[len(result) - amount:]

    def sendMessage(self, dial_id, sender_id, receiver_id, message):
        result = self.database.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name = 'dial_{dial_id}'")
        if not result.first():
            self.createNew(sender_id, receiver_id)
            dial_id = self.database.execute(f"SELECT id FROM dialogues WHERE users ="
                                            f" '{str(sender_id)};{str(receiver_id)}'").first()[0]
            self.sendMessage(dial_id, sender_id, receiver_id, message)
        self.database.execute(f"INSERT INTO dial_{dial_id} (user, time, type, message, new) VALUES({sender_id},"
                              f" datetime('now', 'localtime'), 'text', '{message}', 1)")
        self.database.execute(f"UPDATE dialogues SET last_message_time"
                              f" = datetime('now', 'localtime') WHERE id = {dial_id}")
        self.database.execute(f"UPDATE dialogues SET last_message"
                              f" = '{message}' WHERE id = {dial_id}")

    def sendVideo(self, dial_id, sender_id, receiver_id, path):
        pass

    def sendPhoto(self, dial_id, sender_id, receiver_id, path):
        pass

    def sendAudio(self, dial_id, sender_id, receiver_id, path):
        pass
