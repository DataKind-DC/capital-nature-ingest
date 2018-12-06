import os
import unittest

import wp_etl.loader as loader

import wp_etl.tests.testing_utilities as utilities


if os.environ.get("CAPNAT_TEST_DB") == 'MySQL':
    print('Testing against MySQL')
    USE_MYSQL = True

    USERNAME = os.environ.get("CAPNAT_DB_USER")
    HOST = os.environ.get("CAPNAT_DB_HOST")
    PORT = int(os.environ.get("CAPNAT_DB_PORT"))
    PASSWORD = os.environ.get("CAPNAT_DB_PASSWORD")
    DATABASE = os.environ.get("CAPNAT_DB_DBNAME")

    DatabaseLoader = loader.DatabaseLoader

else:
    print("Testing against SQLite")
    USE_MYSQL = False
    DatabaseLoader = utilities.SqliteDatabaseLoader



class DatabaseLoaderTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.test_data = {
            'events': [
                {
                    'id': 'fdsgfgrewe',
                    'title': 'Some event',
                    'description': 'A really great event, yo.',
                    'image': 'https://caseytrees.org/wp-content/uploads/2018/08/9914c96912bb9d802b693cfb3402753c.jpg',
                    'event_url': 'http://www.someevent.com',
                    'physical_requirements': 'None',
                    'organization_name': 'NPS',
                    'organization_contact_person': 'Joe Bloggs',
                    'organization_phone_number': '202-123-4567',
                    'organization_email': 'something@something.else',
                    'start_date': '2018-12-05',
                    'end_date': '2018-12-05',
                    'start_time': '11:00:00',
                    'end_time': '13:00:00',
                    'all_day': False,
                    'location_venue': 'Somewhere fancy',
                    'location_country': 'USA',
                    'location_address1': '1600 Pennsylvania Ave NW',
                    'location_address2': 'Rm 101',
                    'location_city': 'Washington',
                    'location_state': 'DC',
                    'location_zipcode': '20050',
                    'location_lat': 38.897663,
                    'location_lon': -77.036574,
                    'location_description': 'A really swell kind of place',
                    'location_url': 'http://swellplace.com',
                    'location_phone': '202-765-4321',
                    'is_ticket_required': True,
                    'is_ticket_free': False,
                    'ticket_cost': '$10',
                    'ticketing_url': 'https://www.ticketmaster.com',
                    'registration_by_date': '2018-12-05',
                    'ingesting_script': 'https://github.com/DataKind-DC/capital-nature-ingest/tree/master/ingest_scripts/nps.py',
                    'ingest_source_url': 'https://www.nps.gov',
                    'ingest_source_name': 'National Park Service',
                    'activity_category': 'Park stuff',
                    'activity_tags': ['ice skating', 'outdoors']
                }
            ]
        }
        self.dbl = DatabaseLoader()

    def test_db_connects_and_initializes(self):
        self.assertNotEqual(self.dbl.user_id, None)

    # @unittest.skip
    def test_can_create_post_and_event_rows_in_database(self):
        self.dbl.cursor.execute("SELECT COUNT(*) FROM wp_posts")
        start_posts = self.dbl.cursor.fetchone()[0]
        self.dbl.cursor.execute("SELECT COUNT(*) FROM wp_ai1ec_events")
        start_events = self.dbl.cursor.fetchone()[0]

        self.dbl.load_events(self.test_data)
        new_event_count = len(self.test_data['events'])

        self.dbl.cursor.execute("SELECT COUNT(*) FROM wp_posts")
        end_posts = self.dbl.cursor.fetchone()[0]
        self.assertEqual(end_posts, start_posts + new_event_count)
        self.dbl.cursor.execute("SELECT COUNT(*) FROM wp_ai1ec_events")
        end_events = self.dbl.cursor.fetchone()[0]
        self.assertEqual(end_events, start_events + new_event_count)

    def test_date_parser_correct(self):
        stamp = self.dbl.parse_date('2019-06-01')
        self.assertEqual(stamp.year, 2019)
        self.assertEqual(stamp.month, 6)
        self.assertEqual(stamp.day, 1)

    def test_date_parser_fails_on_datetime_input(self):
        self.assertRaises(ValueError, self.dbl.parse_date, ('2019-06-01 14:43:00'))

    @classmethod
    def tearDownClass(self):
        self.dbl.close()