import unittest
from events.fona import EventbriteIngester, EVENTBRITE_TOKEN, FONA_EVENTBRITE_ORG_ID, handle_fona_eventbrite_api
from tests.fixtures.fona_test_fixtures import events_json, venues_json, organizer_json
import sys
from os import path
import httpretty
import warnings
import json
import requests
import re

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


class EventbriteIngesterTestCase(unittest.TestCase):
    '''
    Test cases for scraping Eventbrite API for Friends of the National Arboretum events.
    '''

    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*")

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
        self.assertEqual(url,
                         f"https://www.eventbriteapi.com/v3/events/search/?token={EVENTBRITE_TOKEN}&organizer.id={FONA_EVENTBRITE_ORG_ID}&")

    @httpretty.activate
    def test_event_transformer(self):
        httpretty.register_uri(httpretty.GET,
                               uri=re.compile(r'https://www.eventbriteapi.com/v3/events/search/.*'),
                               body=events_json.replace("\r", "").replace('"', "\"").replace("\n", ""),  # ev_s,
                               status=200,
                               content_type="application/json")
        httpretty.register_uri(httpretty.GET,
                               uri=re.compile(r'https://www.eventbriteapi.com/v3/venues/.*'),
                               body=venues_json.replace("\r", "").replace('"', "\"").replace("\n", ""),
                               status=200,
                               content_type="application/json")
        httpretty.register_uri(httpretty.GET,
                               uri=re.compile(r'https://www.eventbriteapi.com/v3/organizers/.*'),
                               body=organizer_json.replace("\r", "").replace('"', "\"").replace("\n", ""),
                               status=200,
                               content_type="application/json")
        test_ingester = EventbriteIngester(FONA_EVENTBRITE_ORG_ID)
        test_ingester.scrape()
        for e in test_ingester.output_data.keys():
            print(e, test_ingester.output_data[e])
        self.assertEqual(len(test_ingester.output_data), 2)
        self.assertIn('53882456879', test_ingester.output_data.keys())
        self.assertIn('57800144789', test_ingester.output_data.keys())
        # httpretty.register_uri(httpretty.GET,
        #                        uri="https://www.eventbriteapi.com/",
        #                        body='{"name":"Smoke test","length":10}',
        #                        status=200,
        #                        content_type="application/json")
        # r = requests.get("https://www.eventbriteapi.com/")
        # rj = r.json()
        # self.assertEqual(rj['name'], "Smoke test")


if __name__ == '__main__':
    unittest.main()
