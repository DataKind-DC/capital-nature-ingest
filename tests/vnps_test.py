import unittest
import httpretty
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from events.vnps import parse_date_and_time, get_event_venue_and_categories,\
                        parse_description_and_location, filter_events, \
                        main
from fixtures.vnps_test_fixtures import date_and_time_tag, date_and_time_tag_all_day, \
                                        event_website_content, description_and_location_tag, \
                                        description_and_location_tag_no_venue, events, \
                                        filtered_events, events_page_content, \
                                        text_event_content
from utils import EventDateFormatError, EventTimeFormatError, url_regex, \
                  is_phonenumber_valid, exceptionCallback

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
        self.text_event_content = text_event_content

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
        self.text_event_content = None

    def test_parse_date_and_time(self):
        result = parse_date_and_time(self.date_and_time_tag)
        expected = (False,'19:30:00','21:00:00','2019-02-14','2019-02-14')
        self.assertEqual(result, expected)

    def test_parse_date_and_time_all_day(self):
        result = parse_date_and_time(self.date_and_time_tag_all_day)
        expected = (True, None, None, '2019-03-09', '2019-03-09')
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_get_event_venue_and_categories(self):
        event_website_soup = BeautifulSoup(self.event_website_content, 'html.parser')
        result = get_event_venue_and_categories(event_website_soup)
        expected = ('Blandy Experimental Farm', 'Field Trips, Piedmont')
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_parse_description_and_location(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        result = parse_description_and_location(self.description_and_location_tag)
        expected = (self.event_website,
                    'Identifying Plants in Winter at the Virginia State Arboretum',
                    'Blandy Experimental Farm, Boyce Virginia','Field Trips, Piedmont',
                    'Join Piedmont Chapter Board Member Dr. Emily Southgate who will guide us through the Virginia State Arboretum at Blandy in Clarke County for a special pre-Valentines Day walk on winter plant identification with a stop for hot cocoa.')
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_parse_description_and_location_no_venue(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://vnps.org/events/texas-hill-country-field-trip/',
                               status=200,
                               body=self.text_event_content)
        result = parse_description_and_location(self.description_and_location_tag_no_venue)
        expected = ('https://vnps.org/events/texas-hill-country-field-trip/',
                    'Texas Hill Country Field Trip',
                    '',
                    'Extended Field Trip, Field Trips, State Events',
                    '')
        self.assertEqual(result, expected)

    def test_filter_events(self):
        result = filter_events(self.events, categories = ['Piedmont'])
        expected = self.filtered_events
        self.assertListEqual(result, expected)

    def test_filter_events_no_categories(self):
        result = len(filter_events(self.events, categories = []))
        expected = len(self.events)
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_main(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.events_page,
                               status=200,
                               body=self.events_page_content)
        result = main()
        expected = [{'Event Start Date': '2019-02-09',
                     'Event End Date': '2019-02-09',
                     'Event Start Time': '13:00:00',
                     'Event End Time': '15:00:00',
                     'Event Website': 'https://vnps.org/piedmont/events/identifying-plants-in-winter-at-the-virginia-state-arboretum/',
                     'Event Name': 'Identifying Plants in Winter at the Virginia State Arboretum',
                     'Event Venue Name': 'Blandy Experimental Farm, Boyce Virginia',
                     'All Day Event': False,
                     'Event Description':'Join Piedmont Chapter Board Member Dr. Emily Southgate who will guide us through the Virginia State Arboretum at Blandy in Clarke County for a special pre-Valentines Day walk on winter plant identification with a stop for hot cocoa.',
                     'Event Cost':'',
                     'Event Category': 'Field Trips, Piedmont',
                     'Event Currency Symbol':'$',
                     'Timezone':'America/New_York',
                     'Event Organizers':'Virginia Native Plant Society'}]
        self.assertListEqual(result, expected)

    @httpretty.activate
    def test_main_bad_conn(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.events_page,
                               status=200,
                               body=exceptionCallback)
        result = main()
        expected = []
        self.assertListEqual(result, expected)

    @httpretty.activate
    def test_events_schema_required_fields(self):
        '''
        Tests if the required events fields are present.
        '''
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.events_page,
                               status=200,
                               body=self.events_page_content)
        events = main()
        keys = set().union(*(d.keys() for d in events))
        schema = {'Event Name','Event Description','Event Start Date','Event Start Time',
                  'Event End Date','Event End Time','Timezone','All Day Event',
                  'Event Venue Name','Event Organizers',
                  'Event Cost','Event Currency Symbol',
                  'Event Category','Event Website'}
        result = schema.issubset(keys)
        self.assertTrue(result)
    
    
    @httpretty.activate
    def test_events_schema(self):
        '''
        Tests if all of the event fields conform in name to the schema.
        '''
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.events_page,
                               status=200,
                               body=self.events_page_content)
        events = main()
        keys = set().union(*(d.keys() for d in events))
        schema = {'Do Not Import','Event Name','Event Description','Event Excerpt',
                  'Event Start Date','Event Start Time','Event End Date','Event End Time',
                  'Timezone','All Day Event','Hide Event From Event Listings',
                  'Event Sticky in Month View','Feature Event','Event Venue Name',
                  'Event Organizers','Event Show Map Link',
                  'Event Show Map','Event Cost','Event Currency Symbol',
                  'Event Currency Position','Event Category','Event Tags',
                  'Event Website','Event Featured Image','Allow Comments',
                  'Event Allow Trackbacks and Pingbacks'}
        result = keys.issubset(schema)
        self.assertTrue(result)

    @httpretty.activate
    def test_events_schema_bool_type(self):
        '''
        Tests if the boolean type event fields are bool
        '''
        booleans = ['All Day Event','Hide from Event Listings','Sticky in Month View',
                    'Event Show Map Link','Event Show Map','Allow Comments',
                    'Allow Trackbacks and Pingbacks']
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.events_page,
                               status=200,
                               body=self.events_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event:
                if k in booleans:
                    val = event[k]
                    vals.append(val)
        result = all([isinstance(x, bool) for x in vals])
        self.assertTrue(result)

    @httpretty.activate
    def test_events_schema_string_type(self):
        '''
        Tests if the str and comma delim event field types are strings.
        '''
        comma_delimited = ['Event Venue Name','Event Organizers','Event Category','Event Tags']
        string = ['Event Description','Event Excerpt','Event Name']
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.event_website,
                            status=200,
                            body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.events_page,
                            status=200,
                            body=self.events_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event:
                if k in string or k in comma_delimited:
                    val = event[k]
                    vals.append(val)
        result = all([isinstance(x, str) for x in vals])
        self.assertTrue(result)
    
    @httpretty.activate
    def test_events_schema_currency_symbol_type(self):
        '''
        Tests if the currency symbol is a dollar sign
        '''
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.event_website,
                            status=200,
                            body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.events_page,
                            status=200,
                            body=self.events_page_content)
        events = main()
        for event in events:
            for k in event:
                if k == 'Event Currency Symbol':
                    result = event[k]
                    expected = "$"
                    self.assertEqual(result, expected)
    
    @httpretty.activate
    def test_events_schema_event_cost_type(self):
        '''
        Tests if the event cost is a string of digits
        '''
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.event_website,
                            status=200,
                            body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.events_page,
                            status=200,
                            body=self.events_page_content)
        events = main()
        for event in events:
            for k in event:
                if k == 'Event Cost':
                    val = event[k]
                    #empty strings are "falsy"
                    result = val.isdigit() or not val
                    self.assertTrue(result)

    @httpretty.activate
    def test_events_schema_timezone_type(self):
        '''
        Tests if the timezone event field is 'America/New_York'
        '''
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.event_website,
                            status=200,
                            body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.events_page,
                            status=200,
                            body=self.events_page_content)
        events = main()
        for event in events:
            for k in event:
                if k == 'Timezone':
                    result = event[k]
                    expected = 'America/New_York'
                    self.assertEqual(result, expected)

    @httpretty.activate
    def test_events_schema_date_type(self):
        '''
        Tests if the event start/end date fields are "%Y-%m-%d" 
        Examples:  '1966-01-01' or '1965-12-31'
        '''
        date = ['Event Start Date', 'Event End Date']
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.event_website,
                            status=200,
                            body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.events_page,
                            status=200,
                            body=self.events_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event:
                if k in date:
                    val = event[k]
                    vals.append(val)
        try:
            result = [datetime.strptime(x, "%Y-%m-%d") for x in vals]
        except ValueError:
            result = None
            raise EventDateFormatError
        self.assertIsNotNone(result)

    @httpretty.activate
    def test_events_schema_time_type(self):
        '''
        Tests if the Event Start Time and Event End Time fields follow
        the "%H:%M:%S" format. Examples: '21:30:00' or '00:50:00'
        '''
        time = ['Event Start Time','Event End Time']
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.events_page,
                               status=200,
                               body=self.events_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event: 
                if k in time:
                    val = event[k]
                    vals.append(val)
        try:
            result = [datetime.strptime(x, "%H:%M:%S") for x in vals if x != '']
        except ValueError:
            result = None
            raise EventTimeFormatError
        self.assertIsNotNone(result)
            
    @httpretty.activate
    def test_events_schema_url_type(self):
        '''
        Tests if the event website and event featured image fields contain strings
        that pass Django's test as urls
        '''
        url = ['Event Website','Event Featured Image']
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.event_website,
                            status=200,
                            body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.events_page,
                            status=200,
                            body=self.events_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event: 
                if k in url:
                    val = event[k]
                    vals.append(val)
        result = all([re.match(url_regex, x) for x in vals])
        self.assertTrue(result)

    @httpretty.activate
    def test_events_schema_currency_position_type(self):
        '''
        Tests if the Event Currency Position is 'prefix', 'suffix', or ''
        '''
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.event_website,
                            status=200,
                            body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.events_page,
                            status=200,
                            body=self.events_page_content)
        events = main()
        for event in events:
            for k in event: 
                if k == 'Event Currency Position':
                    val = event[k]
                    expected_vals = ['prefix','suffix','']
                    result = val in expected_vals
                    self.assertTrue(result)

    @httpretty.activate
    def test_events_schema_phone_type(self):
        '''
        Tests if the phone number string is formatted like:  "+1-326-437-9663"
        '''
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.event_website,
                            status=200,
                            body=self.event_website_content)
        httpretty.register_uri(method=httpretty.GET,
                            uri=self.events_page,
                            status=200,
                            body=self.events_page_content)
        events = main()
        for event in events:
            for k in event: 
                if k == 'Event Phone':
                    val = event[k]
                    result = is_phonenumber_valid(val)
                    self.assertTrue(result)
        
if __name__ == '__main__':
    unittest.main()