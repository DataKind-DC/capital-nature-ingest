import unittest
from lambdas.fona.lambda_function import EventbriteIngester, EVENTBRITE_TOKEN, FONA_EVENTBRITE_ORG_ID
from tests.fixtures.fona_test_fixtures import example_eventbrite_json
import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


class EventbriteIngesterTestCase(unittest.TestCase):
    '''
    Test cases for My Events
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_org_url(self):
        ingester = EventbriteIngester(FONA_EVENTBRITE_ORG_ID)
        url = ingester.get_eventbrite_url('/organizers/{id}/', endpoint_params={'id': FONA_EVENTBRITE_ORG_ID})
        self.assertEqual(url,
                         f"https://www.eventbriteapi.com/v3/organizers/{FONA_EVENTBRITE_ORG_ID}/?token={EVENTBRITE_TOKEN}&")

    def test_get_events_url(self):
        ingester = EventbriteIngester(FONA_EVENTBRITE_ORG_ID)
        url = ingester.get_eventbrite_url('/events/search/',
                                          get_params={'token': EVENTBRITE_TOKEN, 'organizer.id': ingester.org_id})
        print(url)
        self.assertEqual(url,
                         f"https://www.eventbriteapi.com/v3/events/search/?token={EVENTBRITE_TOKEN}&organizer.id={FONA_EVENTBRITE_ORG_ID}&")


if __name__ == '__main__':
    unittest.main()
