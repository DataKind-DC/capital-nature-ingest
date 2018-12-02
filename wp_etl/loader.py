import MySQLdb
import os

USERNAME = os.environ.get("CAPNAT_DB_USER")
HOST = os.environ.get("CAPNAT_DB_HOST")
PORT = int(os.environ.get("CAPNAT_DB_PORT"))
PASSWORD = os.environ.get("CAPNAT_DB_PASSWORD")
DATABASE = os.environ.get("CAPNAT_DB_DBNAME")


class DatabaseLoader:

    def __init__(self):
        self.db = MySQLdb.connect(host=HOST, port=PORT, user=USERNAME, passwd=PASSWORD, db=DATABASE)
        self.cursor = self.db.cursor()

    def setup_database(self):
        # 1. Create table for scraped event metadata
        self.cursor.execute("SHOW tables")
        existing_tables = self.cursor.fetchall()
        capnat_meta_exists = False
        for t in existing_tables:
            if t[0] == 'wp_capnat_eventmeta':
                capnat_meta_exists = True
        if capnat_meta_exists == False:
            print("Creating database table to hold event metadata")
            self.cursor.execute("""
                CREATE TABLE wp_capnat_eventmeta (
                    post_id BIGINT(20) PRIMARY KEY,
                    ingester_id VARCHAR(512) NOT NULL,
                    ingester_source_url VARCHAR(512) NOT NULL,
                    ingesting_script VARCHAR(512) NOT NULL
                );
            """)
            print(self.cursor.fetchone())

        # 2. Create a user to associate with uploaded events



if __name__ == "__main__":
    dl = DatabaseLoader()
    dl.setup_database()