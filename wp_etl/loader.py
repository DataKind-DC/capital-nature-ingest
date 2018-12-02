import datetime
import os
import random
import string

import MySQLdb


USERNAME = os.environ.get("CAPNAT_DB_USER")
HOST = os.environ.get("CAPNAT_DB_HOST")
PORT = int(os.environ.get("CAPNAT_DB_PORT"))
PASSWORD = os.environ.get("CAPNAT_DB_PASSWORD")
DATABASE = os.environ.get("CAPNAT_DB_DBNAME")


class DatabaseLoader:

    def __init__(self):
        self.db = MySQLdb.connect(host=HOST, port=PORT, user=USERNAME, passwd=PASSWORD, db=DATABASE)
        self.cursor = self.db.cursor()
        self.user_id = None
        self.setup_database()

    def close(self):
        self.cursor.close()

    def setup_database(self):
        # 1. Create table for scraped event metadata
        self.cursor.execute("SHOW tables")
        existing_tables = self.cursor.fetchall()
        is_table_present = False
        for t in existing_tables:
            if t[0] == 'wp_capnat_eventmeta':
                is_table_present = True
        if is_table_present == False:
            print("Creating database table to hold event metadata")
            self.cursor.execute("""
                CREATE TABLE wp_capnat_eventmeta (
                    post_id BIGINT(20) PRIMARY KEY,
                    ingester_id VARCHAR(512) NOT NULL,
                    ingester_source_url VARCHAR(512) NOT NULL,
                    ingesting_script VARCHAR(512) NOT NULL
                );
            """)

        # 2. Create a user to associate with uploaded events, and get their Wordpress user ID
        self.cursor.execute("""
            SELECT * FROM wp_users WHERE user_login='Capital Nature events'
        """)
        existing_user = self.cursor.fetchall()
        if (len(existing_user)) == 0:
            print("Events user not found... creating new user")
            password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(f"""
                INSERT INTO wp_users (
                    user_login, 
                    user_pass, 
                    user_nicename, 
                    user_email, 
                    user_url, 
                    user_registered, 
                    user_activation_key, 
                    user_status, 
                    display_name )
                VALUES (
                    'Capital Nature events',
                    '{password}',
                    'capital-nature-events',
                    'no-contact@localhost',
                    '',
                    '{now}',
                    '',
                    '0',
                    'Capital Nature events'
                );
            """)
        elif (len(existing_user)) > 1:
            raise ValueError("More than one user exists with the username Capital Nature events")
        self.db.commit()

        self.cursor.execute("SELECT ID FROM wp_users WHERE user_login='Capital Nature events'")
        self.user_id = self.cursor.fetchone()[0]


if __name__ == "__main__":
    dl = DatabaseLoader()
    dl.close()