import unittest
from unittest.mock import patch
import httpretty
import sys
from bs4 import BeautifulSoup
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from events.dug_network import main, soupify_event_page, get_event_location, schematize_event_date, schematize_event_time, get_event_description
from fixtures.dug_test_fixtures import get_event_calendar_soup, input_description, expected_description, event_website_contents, expected_events

class DugNetworkTestCase(unittest.TestCase):
    '''
        Test cases for the DUG Network events
    '''
    def setUp(self):
        self.url = 'http://dugnetwork.org/events/'
        self.event_calendar_uri = 'http://dugnetwork.org/event/sunday-morning-bird-walk-at-dyke-marsh-122/'
        self.expected_events = expected_events
        self.event_calendar_soup = get_event_calendar_soup()
        self.maxDiff = None

    def tearDown(self):
        self.url = None
        # self.event_content = None
        self.event_calendar_soup = None
        self.event_calendar_uri = None
        self.events_result = None

    @httpretty.activate
    def test_event_location(self):
      location = {'@type': 'Place', 'name': 'Dyke Marsh', 'description': '', 'url': False, 'address': {'@type': 'PostalAddress'}, 'telephone': '', 'sameAs': ''}
      expected = 'Dyke Marsh'

      self.assertEqual(get_event_location(location), expected)

    @httpretty.activate
    def test_schematize_event_date(self):
        event_date = '2019-02-10T15:30:00-05:00'
        expected = '2019-02-10'

        self.assertEqual(schematize_event_date(event_date), expected)

    @httpretty.activate
    def test_schematize_event_time(self):
        event_time = '2019-03-06T10:30:52-05:00'
        expected = '10:30:52'

        self.assertEqual(schematize_event_time(event_time), expected)


    @httpretty.activate
    def test_get_event_description(self):
        self.assertEqual(get_event_description(input_description), expected_description)


    @httpretty.activate
    def test_soupify_event_page(self):
        httpretty.register_uri(httpretty.GET,
                               uri=self.event_calendar_uri,
                               body=b'soup',
                               status=200,
                               content_type = "application/json")
        result = soupify_event_page(self.event_calendar_uri)
        expected = BeautifulSoup(b'soup','html.parser')
        self.assertEqual(result, expected)

    @httpretty.activate
    @patch('events.ans.soupify_event_page')
    def test_events_schema(self, mocked_soupify_event_page):
        '''
        Tests if all of the event fields conform in name to the schema.
        '''
        mocked_soupify_event_page.return_value = self.event_calendar_soup
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = main()
        keys = set().union(*(d.keys() for d in events))
        schema = {'Do Not Import', 'Event Name', 'Event Description', 'Event Excerpt',
                  'Event Start Date', 'Event Start Time', 'Event End Date', 'Event End Time',
                  'Timezone', 'All Day Event', 'Hide Event From Event Listings',
                  'Event Sticky in Month View', 'Feature Event', 'Event Venue Name',
                  'Event Organizers', 'Event Show Map Link',
                  'Event Show Map', 'Event Cost', 'Event Currency Symbol',
                  'Event Currency Position', 'Event Category', 'Event Tags',
                  'Event Website', 'Event Featured Image', 'Allow Comments',
                  'Event Allow Trackbacks and Pingbacks'}
        result = keys.issubset(schema)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
