import unittest
from unittest.mock import patch, Mock
import httpretty
from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from events.friends_of_kenilworth_gardens import soupify_event_page, main
from fixtures.friends_test_fixtures import expected_events, get_event_calendar_soup, \
                                       event_website_contents
from utils import EventDateFormatError, EventTimeFormatError, url_regex, \
                  is_phonenumber_valid, exceptionCallback
 
class FRIENDSTestCase(unittest.TestCase):
    '''
    Test cases for the ANS events
    '''

    def setUp(self):
        self.event_calendar_uri = 'http://www.friendsofkenilworthgardens.org/news-and-events/events/2019/03/'
        self.expected_events = expected_events
        self.event_calendar_soup = get_event_calendar_soup()

    def tearDown(self):
        self.event_calendar_uri = None
        self.expected_events = None
        self.event_calendar_soup = None

    @httpretty.activate
    def test_event_location(self):
        location = {'@type': 'Place', 'name': 'Dyke Marsh', 'description': '', 'url': False,
                    'address': {'@type': 'PostalAddress'}, 'telephone': '', 'sameAs': ''}
        expected = 'Dyke Marsh'

        self.assertEqual(get_event_location(location), expected)

    @httpretty.activate
    def test_schematize_event_date(self):
        event_date = '2019-05-25T09:00:00-0400'
        expected = '2019-05-25'

        self.assertEqual(schematize_event_date(event_date), expected)

    @httpretty.activate
    def test_schematize_event_time(self):
        event_time = '2019-03-06T10:30:52-05:00'
        expected = '10:30:52'

        self.assertEqual(schematize_event_time(event_time), expected)

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
    def test_soupify_event_page_exception(self):
        httpretty.register_uri(httpretty.GET,
                               uri=self.event_calendar_uri,
                               body=exceptionCallback,
                               status=200,
                               content_type = "application/json")
        result = soupify_event_page(self.event_calendar_uri)
        expected = None
        self.assertEqual(result, expected)
    



    
    # def test_schematize_event_date(self):
    #     result = schematize_event_date('2019-12-2')
    #     expected = '2019-12-02'
    #     self.assertEqual(result, expected)
    #
    # def test_schematize_event_time(self):
    #     result = schematize_event_time('1:30 pm')
    #     expected = '13:30:00'
    #     self.assertEqual(result, expected)

    @httpretty.activate
    @patch('events.ans.soupify_event_page')
    def test_main(self, mocked_soupify_event_page):
        mocked_soupify_event_page.return_value = self.event_calendar_soup
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        result = main()
        expected = self.expected_events
        self.assertCountEqual(result, expected)
    
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_required_fields(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the required events fields are present.
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     keys = set().union(*(d.keys() for d in events))
    #     schema = {'Event Name','Event Description','Event Start Date','Event Start Time',
    #               'Event End Date','Event End Time','Timezone','All Day Event',
    #               'Event Venue Name','Event Organizers',
    #               'Event Cost','Event Currency Symbol',
    #               'Event Category','Event Website'}
    #     result = schema.issubset(keys)
    #     self.assertTrue(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema(self, mocked_soupify_event_page):
    #     '''
    #     Tests if all of the event fields conform in name to the schema.
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     keys = set().union(*(d.keys() for d in events))
    #     schema = {'Do Not Import','Event Name','Event Description','Event Excerpt',
    #               'Event Start Date','Event Start Time','Event End Date','Event End Time',
    #               'Timezone','All Day Event','Hide Event From Event Listings',
    #               'Event Sticky in Month View','Feature Event','Event Venue Name',
    #               'Event Organizers','Event Show Map Link',
    #               'Event Show Map','Event Cost','Event Currency Symbol',
    #               'Event Currency Position','Event Category','Event Tags',
    #               'Event Website','Event Featured Image','Allow Comments',
    #               'Event Allow Trackbacks and Pingbacks'}
    #     result = keys.issubset(schema)
    #     self.assertTrue(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_bool_type(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the boolean type event fields are bool
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     booleans = ['All Day Event','Hide from Event Listings','Sticky in Month View',
    #                 'Event Show Map Link','Event Show Map','Allow Comments',
    #                 'Allow Trackbacks and Pingbacks']
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     vals = []
    #     for event in events:
    #         for k in event:
    #             if k in booleans:
    #                 val = event[k]
    #                 vals.append(val)
    #     result = all([isinstance(x, bool) for x in vals])
    #     self.assertTrue(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_string_type(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the str and comma delim event field types are strings.
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     comma_delimited = ['Event Venue Name','Event Organizers','Event Category','Event Tags']
    #     string = ['Event Description','Event Excerpt','Event Name']
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     vals = []
    #     for event in events:
    #         for k in event:
    #             if k in string or k in comma_delimited:
    #                 val = event[k]
    #                 vals.append(val)
    #     result = all([isinstance(x, str) for x in vals])
    #     self.assertTrue(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_currency_symbol_type(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the currency symbol is a dollar sign
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     vals = []
    #     for event in events:
    #         for k in event:
    #             if k == 'Event Currency Symbol':
    #                 vals.append(event[k])
    #     result = all([x=='$' for x in vals])
    #     self.assertTrue(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_event_cost_type(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the event cost is a string of digits
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     vals = []
    #     for event in events:
    #         for k in event:
    #             if k == 'Event Cost':
    #                 val = event[k]
    #                 vals.append(val)
    #     #empty strings are "falsy"
    #     result = all(x.isdigit() or not x for x in vals)
    #     self.assertTrue(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_timezone_type(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the timezone event field is 'America/New_York'
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     vals = []
    #     for event in events:
    #         for k in event:
    #             if k == 'Timezone':
    #                 val = event[k]
    #                 vals.append(val)
    #     result = all(x == 'America/New_York' for x in vals)
    #     self.assertTrue(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_date_type(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the event start/end date fields are "%Y-%m-%d"
    #     Examples:  '1966-01-01' or '1965-12-31'
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     date = ['Event Start Date', 'Event End Date']
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     vals = []
    #     for event in events:
    #         for k in event:
    #             if k in date:
    #                 val = event[k]
    #                 vals.append(val)
    #     try:
    #         result = [datetime.strptime(x, "%Y-%m-%d") for x in vals]
    #     except ValueError:
    #         result = None
    #         raise EventDateFormatError
    #     self.assertIsNotNone(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_time_type(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the Event Start Time and Event End Time fields follow
    #     the "%H:%M:%S" format. Examples: '21:30:00' or '00:50:00'
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     time = ['Event Start Time','Event End Time']
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     vals = []
    #     for event in events:
    #         for k in event:
    #             if k in time:
    #                 val = event[k]
    #                 vals.append(val)
    #     try:
    #         result = [datetime.strptime(x, "%H:%M:%S") for x in vals if x != '']
    #     except ValueError:
    #         result = None
    #         raise EventTimeFormatError
    #     self.assertIsNotNone(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_url_type(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the event website and event featured image fields contain strings
    #     that pass Django's test as urls
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     url = ['Event Website','Event Featured Image']
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     vals = []
    #     for event in events:
    #         for k in event:
    #             if k in url:
    #                 val = event[k]
    #                 vals.append(val)
    #     result = all([re.match(url_regex, x) for x in vals])
    #     self.assertTrue(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_currency_position_type(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the Event Currency Position is 'prefix', 'suffix', or ''
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     for event in events:
    #         for k in event:
    #             if k == 'Event Currency Position':
    #                 val = event[k]
    #                 expected_vals = ['prefix','suffix','']
    #                 result = val in expected_vals
    #                 self.assertTrue(result)
    #
    # @httpretty.activate
    # @patch('events.ans.soupify_event_page')
    # def test_events_schema_phone_type(self, mocked_soupify_event_page):
    #     '''
    #     Tests if the phone number string is formatted like:  "+1-326-437-9663"
    #     '''
    #     mocked_soupify_event_page.return_value = self.event_calendar_soup
    #     for event_website_content in event_website_contents:
    #         event_website = list(event_website_content.keys())[0]
    #         content = event_website_content[event_website]
    #         httpretty.register_uri(httpretty.GET,
    #                                uri=event_website,
    #                                body=content,
    #                                status=200)
    #     events = main()
    #     for event in events:
    #         for k in event:
    #             if k == 'Event Phone':
    #                 val = event[k]
    #                 result = is_phonenumber_valid(val)
    #                 self.assertTrue(result)
        
if __name__ == '__main__':
    unittest.main()