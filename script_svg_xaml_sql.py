import sqlite3


class database:

    def __init__(self):
        base = "data.sqlite"
        self.conn = sqlite3.connect(base)
        self.conn.row_factory = self.dict_factory
        self.cursor = self.conn.cursor()

    def dict_factory(self, cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def close(self):
        self.cursor.close()
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def execute(self, cmd: str):
        return self.cursor.execute(cmd)

    def read_all(self, table: str):
        return self.execute(f"SELECT * FROM {table}").fetchall()

    def create_table_style_tmp(self, table="t_tmp_style"):
        self.execute(f"DROP TABLE IF EXISTS {table};")

        cmd = f"""CREATE TABLE {table}(id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            class TEXT NOT NULL,
                                            value TEXT NOT NULL);"""
        self.execute(cmd)

        return table

    def reset_table(self, table: str):
        for cmd in [f"DELETE FROM {table};", f"DELETE FROM sqlite_sequence WHERE name='{table}';"]:
            self.execute(cmd)
        self.commit()

    def delete_table(self, table):
        for cmd in [f"DROP TABLE {table};", f"DELETE FROM sqlite_sequence WHERE name='{table}';"]:
            self.execute(cmd)
        self.commit()

    def insert_style(self, key: str, value: str, table="t_tmp_style", key_name="class", value_name="value"):
        cmd = f"INSERT INTO {table}({key_name}, {value_name}) VALUES ('{key}', '{value}')"
        self.execute(cmd)
        self.commit()


if __name__ == '__main__':
    connector = database()

    # table = connector.create_table_style_tmp()
    connector.insert_style("st0", "salut")
    connector.delete_table(table="t_tmp_style")
