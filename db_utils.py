# Not working
from datetime import datetime

import MySQLdb
import sshtunnel

sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0


class DB:
    def __init__(self, config: dict):
        self.conn = None
        self.server = None
        self.config = config

    def connect(self):
        if self.config["use_ssh"]:
            self.server = sshtunnel.open_tunnel(
                self.config["ssh_host"],
                ssh_username=self.config["ssh_user"],
                ssh_password=self.config["ssh_pass"],
                remote_bind_address=(
                    self.config["mysql_host"],
                    self.config["mysql_port"],
                ),
                local_bind_address=("127.0.0.1", self.config["forward_port"]),
                debug_level="TRACE",
            )
            self.server.start()

        self.conn = MySQLdb.connect(
            host="127.0.0.1",
            db=self.config["mysql_dbname"],
            user=self.config["mysql_user"],
            passwd=self.config["mysql_pass"],
            port=self.server.local_bind_port
            if self.config["use_ssh"]
            else self.config["mysql_port"],
            connect_timeout=10,
        )

    def close(self):
        self.server.close()
        self.conn.close()

    def query(self, sql):
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        return cursor


def insert_row(db: DB, table_name: str, username: str, chat_id: str) -> bool:
    """
    Connect to database and execute INSERT INTO query
    :param table_name: table for storing data
    :param username: telegram username
    :param chat_id: id of chat between bot and user
    :return: success status
    """
    query = """
                INSERT INTO {}
                (username, chat_id, started_at) 
                VALUES ('{}','{}','{}')
                """.format(
        table_name, username, chat_id, datetime.now()
    )
    print(query)
    result = db.query(query)

    return result
