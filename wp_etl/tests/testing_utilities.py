import os
import random
import sqlite3
import string

import wp_etl.loader as loader

class SqliteDatabaseLoader(loader.DatabaseLoader):
    def __init__(self, reset_db = True):
        if reset_db == True and 'test.db' in os.listdir(os.getcwd()):
            os.remove('test.db')
        self.db = sqlite3.connect('test.db')
        self.cursor = self.db.cursor()
        self.user_id = None
        self.setup_database()
        self.param_symbol = '?'

    def setup_database(self):
        # 1. Create basic tables
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS wp_users (
                    ID INTEGER PRIMARY KEY,
                    user_login TEXT,
                    user_pass TEXT,
                    user_nicename TEXT,
                    user_email TEXT,
                    user_url TEXT,
                    user_registered TEXT,
                    user_activation_key TEXT,
                    user_status INTEGER,
                    display_name TEXT
                );
            """)
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS wp_posts (
                    ID INTEGER PRIMARY KEY DEFAULT NULL,
                    post_author INTEGER DEFAULT 0,
                    post_date TEXT DEFAULT '0000-00-00 00:00:00',
                    post_date_gmt TEXT DEFAULT '0000-00-00 00:00:00',
                    post_content TEXT DEFAULT NULL,
                    post_title TEXT DEFAULT NULL,
                    post_excerpt TEXT DEFAULT NULL,
                    post_status TEXT DEFAULT 'publish',
                    comment_status TEXT DEFAULT 'open',
                    post_password TEXT,
                    post_name TEXT,
                    to_ping TEXT DEFAULT NULL,
                    pinged TEXT DEFAULT NULL,
                    post_modified TEXT DEFAULT '0000-00-00 00:00:00',
                    post_modified_gmt TEXT DEFAULT '0000-00-00 00:00:00',
                    post_content_filtered TEXT DEFAULT NULL,
                    post_parent INTEGER DEFAULT 0,
                    guid TEXT,
                    menu_order INTEGER DEFAULT 0,
                    post_type TEXT DEFAULT 'post',
                    post_mime_type TEXT,
                    comment_count INTEGER DEFAULT 0
                )
            """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS wp_ai1ec_events (
                post_id INTEGER PRIMARY KEY DEFAULT NULL,
                start INTEGER DEFAULT NULL,
                end INTEGER DEFAULT NULL,
                timezone_name TEXT DEFAULT NULL,
                allday INTEGER DEFAULT NULL,
                instant_event INTEGER DEFAULT 0,
                recurrence_rules TEXT DEFAULT NULL,
                exception_rules TEXT DEFAULT NULL,
                recurrence_dates TEXT DEFAULT NULL,
                exception_dates TEXT DEFAULT NULL,
                venue TEXT DEFAULT NULL,
                country TEXT DEFAULT NULL,
                address TEXT DEFAULT NULL,
                city TEXT DEFAULT NULL,
                province TEXT DEFAULT NULL,
                postal_code TEXT DEFAULT NULL,
                show_map INTEGER DEFAULT NULL,
                contact_name TEXT DEFAULT NULL,
                contact_phone TEXT DEFAULT NULL,
                contact_email TEXT DEFAULT NULL,
                contact_url TEXT DEFAULT NULL,
                cost TEXT DEFAULT NULL,
                ticket_url TEXT DEFAULT NULL,
                ical_feed_url TEXT DEFAULT NULL,
                ical_source_organizer TEXT DEFAULT NULL,
                ical_contact TEXT DEFAULT NULL,
                ical_uid TEXT DEFAULT NULL,
                show_coordinates INTEGER DEFAULT NULL,
                latitude REAL DEFAULT NULL,
                longitude REAL DEFAULT NULL,
                force_regenerate INTEGER DEFAULT 0
            )
        """)

        # 2. Create table of ai1ec event instances
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS wp_ai1ec_event_instances (
                id INTEGER PRIMARY KEY,
                post_id INTEGER NOT NULL,
                start INTEGER NOT NULL,
                end INTEGER NOT NULL
            );
        """)

        # 3. Create table for scraped event metadata
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS wp_capnat_eventmeta (
                ingester_id TEXT PRIMARY KEY,
                post_id INTEGER NOT NULL,
                ingester_source_url TEXT NOT NULL,
                ingesting_script TEXT NOT NULL
            );
        """)

        # 4. Create a user to associate with uploaded events, and get their Wordpress user ID
        self.cursor.execute("""
            SELECT * FROM wp_users WHERE user_login='Capital Nature events'
        """)
        existing_user = self.cursor.fetchall()
        if (len(existing_user)) == 0:
            print("Events user not found... creating new user")
            password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
            now = self.get_now_timestamp()
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

        self.cursor.execute("SELECT ID FROM wp_users WHERE user_login='Capital Nature events'")
        self.user_id = self.cursor.fetchone()[0]

