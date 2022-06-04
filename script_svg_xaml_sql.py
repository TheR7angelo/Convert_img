import sqlite3
import os


class database:

    def __init__(self, file="data.sqlite"):

        self.base = file

        self.conn = sqlite3.connect(file)
        self.conn.row_factory = self.dict_factory
        self.cursor = self.conn.cursor()

    def dict_factory(self, cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def commit(self):
        self.conn.commit()

    def execute(self, cmd: str):
        return self.cursor.execute(cmd)

    def close(self):
        self.cursor.close()
        self.conn.close()

    def delete(self):
        os.remove(self.base)

    def read_all(self, table: str):
        return self.execute(f"SELECT * FROM {table}").fetchall()

    def create_table_style_tmp(self, table="t_tmp_style"):
        self.execute(f"DROP TABLE IF EXISTS {table};")

        cmd = f"""CREATE TABLE {table}(id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            class TEXT NOT NULL,
                                            type TEXT NOT NULL,
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

    def insert_style(self, key: str, type_value: str, value: str, table="t_tmp_style", key_name="class", type_name="type", value_name="value"):
        cmd = f"INSERT INTO {table}({key_name}, {type_name}, {value_name}) VALUES ('{key}', '{type_value}','{value}')"
        self.execute(cmd)

    def find_value(self, key_name: str, value: str, table="t_tmp_style"):
        cmd = f"SELECT * FROM {table} WHERE {key_name}='{value}';"
        return self.execute(cmd).fetchall()


if __name__ == '__main__':
    connector = database()

    # table = connector.create_table_style_tmp()
    # connector.insert_style("st0", "salut")
    # connector.delete_table(table="t_tmp_style")
