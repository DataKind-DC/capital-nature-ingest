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

    def setUp(self):
        self.test_data = {
            'events': [
                {
                    'id': 'fdsgfgrewe',
                    'title': 'Some event',
                    'description': 'A really great event, yo.',
                    'image': 'https://caseytrees.org/wp-content/uploads/2018/08/9914c96912bb9d802b693cfb3402753c.jpg',
                    'physical_requirements': 'None',
                    'organizer': {
                        'organization_name': 'NPS',
                        'contact_person': 'Joe Bloggs',
                        'phone_number': '202-123-4567',
                        'email': 'something@something.else'
                    },
                    'timing': {
                        'start_date': '2018-12-05',
                        'end_date': '2018-12-05',
                        'start_time': '11:00:00',
                        'end_time': '13:00:00',
                        'all_day': False
                    },
                    'location': {
                        'venue': 'Somewhere fancy',
                        'country': 'USA',
                        'address1': '1600 Pennsylvania Ave NW',
                        'address2': 'Rm 101',
                        'city': 'Washington',
                        'state': 'DC',
                        'postal_code': '20050',
                        'lat': 38.897663,
                        'long': -77.036574,
                        'location_description': 'A really swell kind of place',
                        'location_url': 'http://swellplace.com',
                        'location_phone': '202-765-4321'
                    },
                    'ticketing': {
                        'is_required': True,
                        'is_free': False,
                        'cost': '$10',
                        'ticketing_url': 'https://www.ticketmaster.com',
                        'registration_by_date': '2018-12-05'
                    },
                    'metadata': {
                        'ingesting_script': 'https://github.com/DataKind-DC/capital-nature-ingest/tree/master/ingest_scripts/nps.py',
                        'ingest_source_url': 'https://www.nps.gov',
                        'ingest_source_name': 'National Park Service',
                        'activity_category': 'Park stuff',
                        'activity_tags': ['ice skating', 'outdoors']
                    }
                }
            ]
        }
        self.dbl = DatabaseLoader()

    def test_db_connects_and_initializes(self):
        self.assertNotEqual(self.dbl.user_id, None)
