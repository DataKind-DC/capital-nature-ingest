import datetime
import os
import random
import string
import time

import MySQLdb


class DatabaseLoader:

    def __init__(self):
        self.db = MySQLdb.connect(
            host=os.environ.get("CAPNAT_DB_HOST"),
            port=int(os.environ.get("CAPNAT_DB_PORT")),
            user=os.environ.get("CAPNAT_DB_USER"),
            passwd=os.environ.get("CAPNAT_DB_PASSWORD"),
            db=os.environ.get("CAPNAT_DB_DBNAME")
        )
        self.cursor = self.db.cursor()
        self.user_id = None
        self.setup_database()

    def close(self):
        self.cursor.close()
        self.db.commit()

    def setup_database(self):
        # 1. Create table for scraped event metadata
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS wp_capnat_eventmeta (
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
        # self.db.commit()

        self.cursor.execute("SELECT ID FROM wp_users WHERE user_login='Capital Nature events'")
        self.user_id = self.cursor.fetchone()[0]

    def load_events(self, event_data):
        for e in event_data['events']:
            # TODO: Check if exists in event metadata table, and skip if so.
            print('processing event:', e['id'])
            now = self.get_now_timestamp()
            self.cursor.execute("""
                INSERT INTO wp_posts
                    (post_author, post_date, post_content, post_title, post_status, post_type)
                VALUES 
                    (?,           ?,         ?,            ?,         'pending',   'ai1ec_event')
            """, (self.user_id, now, e['description'], e['title']))
            post_id = self.cursor.lastrowid
            values = self.generate_ai1ec_fields(e, post_id)
            self.cursor.execute("""
                INSERT INTO wp_ai1ec_events
                    (post_id, start, end, timezone_name, allday, instant_event, venue, country, address, city, province,
                     postal_code, show_map, contact_name, contact_phone, contact_email, contact_url, cost, ticket_url,
                     show_coordinates, longitude, latitude)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)
        # self.cursor.close()
        self.db.commit()

    def get_now_timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def parse_date(self, stamp):
        return datetime.datetime.strptime(stamp, '%Y-%m-%d')

    def parse_time(self, stamp):
        return datetime.datetime.strptime(stamp, '%H:%M:%S')

    def generate_ai1ec_fields(self, event, post_id):
        values = [post_id]
        start_date = self.parse_date(event['start_date'])
        start_time = self.parse_time(event['start_time'])
        values.append(datetime.datetime(
            start_date.year, start_date.month, start_date.day,
            start_time.hour, start_time.minute).timestamp())
        end_date = self.parse_date(event['end_date'])
        end_time = self.parse_time(event['end_time'])
        values.append(datetime.datetime(
            end_date.year, end_date.month, end_date.day,
            end_time.hour, end_time.minute).timestamp())
        values.append('America/New_York')
        if event['all_day'] == True:
            values.append(1)
        else:
            values.append(0)
        values.append(0) # 'instant event'
        values.append(event['location_venue'])
        values.append('United States')
        values.append(event['location_address1']) #+', '+event['location']['address2'])
        values.append(event['location_city'])
        values.append(event['location_state'])
        values.append(event['location_zipcode'])
        values.append(1) # show map
        values.append(event['organization_name'])
        values.append(event['organization_phone_number'])
        values.append(event['organization_email'])
        values.append(event['event_url'])
        values.append(event['ticket_cost'])
        values.append(event['ticketing_url'])
        values.append(1) #show coordinates
        values.append(event['location_lat'])
        values.append(event['location_lon'])
        return values


if __name__ == "__main__":
    dl = DatabaseLoader()
    dl.close()