import unittest
from unittest.mock import patch, Mock
import httpretty
import requests

from lambda_function import parse_date_and_time, get_event_venue_and_categories, parse_description_and_location, \
                            filter_events, get_vnps_events
from test_fixtures import date_and_time_tag, date_and_time_tag_all_day, event_website_content, \
                          description_and_location_tag, description_and_location_tag_no_venue, \
                          events, filtered_events, events_page_content
                          

def exceptionCallback(request, uri, headers):
    '''
    Create a callback body that raises an exception when opened. This simulates a bad request.
    '''
    raise requests.ConnectionError('Raising a connection error for the test. You can ignore this!')

class VNPSTestCase(unittest.TestCase):
    '''
    Test cases for VNPS events.
    '''

    def setUp(self):
        self.date_and_time_tag = date_and_time_tag()
        self.date_and_time_tag_all_day = date_and_time_tag_all_day()
        self.event_website = 'https://vnps.org/piedmont/events/identifying-plants-in-winter-at-the-virginia-state-arboretum/'
        self.event_website_content = event_website_content
        self.description_and_location_tag = description_and_location_tag()
        self.description_and_location_tag_no_venue = description_and_location_tag_no_venue()
        self.events = events
        self.filtered_events = filtered_events
        self.events_page = 'https://vnps.org/events/'
        self.events_page_content = events_page_content

    def tearDown(self):
        self.date_and_time_tag = None
        self.date_and_time_tag_all_day = None
        self.event_website = None
        self.event_website_content = None
        self.description_and_location_tag = None
        self.description_and_location_tag_no_venue = None
        self.events = None
        self.filtered_events = None
        self.events_page = None
        self.events_page_content = None

    def test_parse_date_and_time(self):
        result = parse_date_and_time(self.date_and_time_tag)
        expected = (False,'7:30 pm','9:00 pm','Thursday, February 14, 2019','Thursday, February 14, 2019')
        self.assertTupleEqual(result, expected)

    def test_parse_date_and_time_all_day(self):
        result = parse_date_and_time(self.date_and_time_tag_all_day)
        expected = (True, None, None, 'Saturday, March 9, 2019', 'Saturday, March 9, 2019')
        self.assertTupleEqual(result, expected)
    
    @httpretty.activate
    def test_get_event_venue_and_categories_conn_error(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=exceptionCallback)
        result = get_event_venue_and_categories(self.event_website)
        expected = (None, None)
        self.assertTupleEqual(result, expected)

    @httpretty.activate
    def test_get_event_venue_and_categories(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        result = get_event_venue_and_categories(self.event_website)
        expected = ('Blandy Experimental Farm', 'Field Trips, Piedmont')
        self.assertTupleEqual(result, expected)

    def test_parse_description_and_location(self):
        result = parse_description_and_location(self.description_and_location_tag)
        expected = ('https://vnps.org/piedmont/events/identifying-plants-in-winter-at-the-virginia-state-arboretum/',
                    'Identifying Plants in Winter at the Virginia State Arboretum',
                    'Blandy Experimental Farm, Boyce Virginia','Field Trips, Piedmont')
        self.assertTupleEqual(result, expected)

    def test_parse_description_and_location_no_venue(self):
        result = parse_description_and_location(self.description_and_location_tag_no_venue)
        expected = ('https://vnps.org/events/texas-hill-country-field-trip/',
                    'Texas Hill Country Field Trip',
                    '',
                    'Extended Field Trip, Field Trips, State Events')
        self.assertTupleEqual(result, expected)

    def test_filter_events(self):
        result = filter_events(self.events, categories = ['Piedmont'])
        expected = self.filtered_events
        self.assertListEqual(result, expected)

    def test_filter_events_no_categories(self):
        result = len(filter_events(self.events, categories = []))
        expected = len(self.events)
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_get_vnps_events(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.events_page,
                               status=200,
                               body=self.events_page_content)
        result = get_vnps_events()
        expected = [{'Event Start Date': 'Saturday, February 9, 2019',
                     'Event End Date': 'Saturday, February 9, 2019',
                     'Event Start Time': '1:00 pm',
                     'Event End Time': '3:00 pm',
                     'Event Website': 'https://vnps.org/piedmont/events/identifying-plants-in-winter-at-the-virginia-state-arboretum/',
                     'Event Name': 'Identifying Plants in Winter at the Virginia State Arboretum',
                     'Event Venue Name': 'Blandy Experimental Farm, Boyce Virginia',
                     'All Day Event': False,
                     'Event Tags': 'Field Trips, Piedmont',
                     'Event Currency Symbol':'$',
                     'Event Time Zone':'Eastern Standard Time',
                     'Event Organizer Name(s) or ID(s)':'Blandy Experimental Farm, Boyce Virginia'}]
        self.assertListEqual(result, expected)

    @httpretty.activate
    def test_get_vnps_events_bad_conn(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.events_page,
                               status=200,
                               body=exceptionCallback)
        result = get_vnps_events()
        expected = []
        self.assertListEqual(result, expected)

    @httpretty.activate
    def test_events_schema(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.events_page,
                               status=200,
                               body=self.events_page_content)
        events = get_vnps_events()
        keys = set().union(*(d.keys() for d in events))
        schema = {'Do Not Import','Event Name','Event Description','Event Excerpt',
                  'Event Start Date','Event Start Time','Event End Date','Event End Time',
                  'Event Time Zone','All Day Event','Hide Event From Event Listings',
                  'Event Sticky in Month View','Feature Event','Event Venue Name',
                  'Event Organizer Name(s) or ID(s)','Event Show Map Link',
                  'Event Show Map','Event Cost','Event Currency Symbol',
                  'Event Currency Position','Event Category','Event Tags',
                  'Event Website','Event Featured Image','Event Allow Comments',
                  'Event Allow Trackbacks and Pingbacks'}
        result = keys.issubset(schema)
        expected = True
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()

        