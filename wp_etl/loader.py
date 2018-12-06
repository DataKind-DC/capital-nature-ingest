import datetime
import os
import random
import string
import time

import MySQLdb


class DatabaseLoader:

    def __init__(self, host=None, port=None, user=None, passwd=None, db=None):
        if host == None:
            host = os.environ.get("CAPNAT_DB_HOST")
        if port == None:
            port = int(os.environ.get("CAPNAT_DB_PORT"))
        if user == None:
            user = os.environ.get("CAPNAT_DB_USER")
        if passwd == None:
            passwd = os.environ.get("CAPNAT_DB_PASSWORD")
        if db == None:
            db = os.environ.get("CAPNAT_DB_DBNAME")
        self.db = MySQLdb.connect(
            host=host,
            port=port,
            user=user,
            passwd=passwd,
            db=db
        )
        self.db.set_character_set('utf8')
        self.cursor = self.db.cursor()
        self.cursor.execute('SET NAMES utf8;')
        self.cursor.execute('SET CHARACTER SET utf8;')
        self.cursor.execute('SET character_set_connection=utf8;')
        self.user_id = None
        self.setup_database()
        self.param_symbol = '%s'

    def close(self):
        self.cursor.close()
        self.db.commit()

    def setup_database(self):
        # 1. Create table for scraped event metadata
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS wp_capnat_eventmeta (
                ingester_id VARCHAR(512) PRIMARY KEY,
                post_id BIGINT(20) NOT NULL,
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
            print('processing event:', e['id'])
            self.cursor.execute(f"SELECT count(*) FROM wp_capnat_eventmeta WHERE ingester_id = {self.param_symbol}", (e['id'], ))
            if self.cursor.fetchone()[0] > 0:
                print(" - event with that ID already exists in database")
                continue
            print(" - adding to database")
            now = self.get_now_timestamp()
            self.cursor.execute(f"""
                INSERT INTO wp_posts
                    (post_author, post_date, post_date_gmt, post_content, post_title, post_excerpt, post_status, to_ping, pinged, post_modified, 
                     post_modified_gmt, post_content_filtered, post_type)
                VALUES 
                    ({self.param_symbol}, {self.param_symbol}, {self.param_symbol}, {self.param_symbol}, 
                     {self.param_symbol}, '', 'pending', '', '', {self.param_symbol}, {self.param_symbol}, '', 'ai1ec_event')
            """, (self.user_id, now, now, e['description'], e['title'], now, now))
            post_id = self.cursor.lastrowid
            print(" post id is", post_id)
            values = self.generate_ai1ec_fields(e, post_id)
            self.cursor.execute(f"""
                INSERT INTO wp_ai1ec_events
                    (post_id, start, end, timezone_name, allday, instant_event, venue, country, address, city, province,
                     postal_code, show_map, contact_name, contact_phone, contact_email, contact_url, cost, ticket_url,
                     show_coordinates, longitude, latitude)
                VALUES
                    ({self.param_symbol}, {self.param_symbol}, {self.param_symbol}, {self.param_symbol}, 
                     {self.param_symbol}, {self.param_symbol}, {self.param_symbol}, {self.param_symbol}, 
                     {self.param_symbol}, {self.param_symbol}, {self.param_symbol}, {self.param_symbol}, 
                     {self.param_symbol}, {self.param_symbol}, {self.param_symbol}, {self.param_symbol},
                     {self.param_symbol}, {self.param_symbol}, {self.param_symbol}, {self.param_symbol}, 
                     {self.param_symbol}, {self.param_symbol})
            """, values)

            self.cursor.execute(f"""
                    INSERT INTO wp_ai1ec_event_instances
                        (post_id, start, end)
                    VALUES
                        ({self.param_symbol}, {self.param_symbol}, {self.param_symbol})
                """, values[:3])
            self.cursor.execute(f"""
                    INSERT INTO wp_capnat_eventmeta
                        (post_id, ingester_id, ingester_source_url, ingesting_script)
                    VALUES
                        ({self.param_symbol}, {self.param_symbol}, {self.param_symbol}, {self.param_symbol})
                """, (post_id, e["id"], e["ingest_source_url"], e['ingesting_script']))

            self.db.commit()

    def get_now_timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def posix_date(self, d, t):
        if t == None:
            t = datetime.time(0, 0, 0)
        return datetime.datetime.combine(d, t).timestamp()

    def generate_ai1ec_fields(self, event, post_id):
        values = [post_id]

        values.append(self.posix_date(event['start_date'], event['start_time']))

        if event['end_date'] != None: # estimate end time based on start time
            if event['start_time'] == None: # if event "starts" at midnight, then it ends the following midnight
                values.append(values[-1] + 86400)
            else: # otherwise estimate dureation at 1 hour
                values.append(values[-1] + 3600)

        values.append('America/New_York')
        if event['all_day'] == True: # TODO: combine with start and end times to determine all_day better. What does all_day even mean?
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
        return values


if __name__ == "__main__":
    dl = DatabaseLoader()
    dl.close()