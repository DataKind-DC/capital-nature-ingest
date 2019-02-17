import unittest
from unittest.mock import patch, Mock
import httpretty
import requests
import re
from datetime import datetime
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from lambdas.arlington.lambda_function import get_arlington_events, html_textraction, parse_event_name, \
                            schematize_events, schematize_date
from fixtures.arlington_test_fixtures import page_one_uri_json, page_two_uri_json, page_one_uri_event_items, \
                          page_two_uri_event_items, schematized_page_two_event_items
from utils import EventDateFormatError, EventTimeFormatError, url_regex, \
                  is_phonenumber_valid, exceptionCallback

class ArlingtonTestCase(unittest.TestCase):
    '''
    Test cases for the Arlington events
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @httpretty.activate
    def test_get_arlington_events(self):
        page_one_uri = 'https://today-service.arlingtonva.us/api/event/elasticevent?&StartDate=2019-01-25T05:00:00.000Z&EndDate=null&TopicCode=ANIMALS&TopicCode=ENVIRONMENT&ParkingAvailable=false&NearBus=false&NearRail=false&NearBikeShare=false&From=0&Size=5&OrderBy=featured&EndTime=86400000'
        page_two_uri = 'https://today-service.arlingtonva.us/api/event/elasticevent?&StartDate=2019-01-25T05:00:00.000Z&EndDate=null&TopicCode=ANIMALS&TopicCode=ENVIRONMENT&ParkingAvailable=false&NearBus=false&NearRail=false&NearBikeShare=false&From=5&Size=5&OrderBy=featured&EndTime=86400000'
        httpretty.register_uri(httpretty.GET,
                               uri=page_one_uri,
                               body=page_one_uri_json,
                               status=200,
                               content_type = "application/json")

        httpretty.register_uri(httpretty.GET,
                               uri=page_two_uri,
                               body=page_two_uri_json,
                               status=200,
                               content_type = "application/json")
        result = get_arlington_events()
        expected = page_one_uri_event_items + page_two_uri_event_items
        self.assertCountEqual(result, expected)

    def test_html_textraction(self):
        text = '<p>Families age 3 and up. Register children and adults; children must be accompanied by a registered adult. We&#8217;ll use all sorts of cookies, marshmallows and toppings for the most decadent campfire s&#8217;mores ever! For information: 703-228-6535. Meet at Long Branch Nature Center. Registration Required: Resident registration begins at 8:00am on 11/13/2018. Non-resident registration begins at 8:00am on 11/14/2018.</p>\n<p>Activity #:\xa0622959 &#8211; O</p>\n'
        result = html_textraction(text)
        expected = 'Families age 3 and up. Register children and adults; children must be accompanied by a registered adult. We’ll use all sorts of cookies, marshmallows and toppings for the most decadent campfire s’mores ever! For information: 703-228-6535. Meet at Long Branch Nature Center. Registration Required: Resident registration begins at 8:00am on 11/13/2018. Non-resident registration begins at 8:00am on 11/14/2018.'
        self.assertEqual(result, expected)

    def test_parse_event_name_rip_case_one(self):
        event_name = 'RiP – Tuckahoe Park Invasive Plant Removal'
        result = parse_event_name(event_name)
        expected = 'Tuckahoe Park Invasive Plant Removal'
        self.assertEqual(result, expected)

    def test_parse_event_name_rip_case_two(self):
        event_name = 'RiP – Tuckahoe Park'
        result = parse_event_name(event_name)
        expected = 'Tuckahoe Park Invasive Plant Removal'
        self.assertEqual(result, expected)

    def test_parse_event_name(self):
        event_name = 'Annual Four Mile  Run Stream Cleanup'
        result = parse_event_name(event_name)
        expected = 'Annual Four Mile Run Stream Cleanup'
        self.assertEqual(result, expected)

    def test_schematize_date(self):
        result = schematize_date('2019-01-25T00:00:00')
        expected = '2019-01-25'
        self.assertEqual(result, expected)
    
    def test_schematize_events(self):
        result = schematize_events(page_two_uri_event_items)
        expected = schematized_page_two_event_items
        self.assertCountEqual(result, expected)

    def test_events_schema_required_fields(self):
        '''
        Tests if the required events fields are present.
        '''
        events = schematize_events(page_two_uri_event_items)
        keys = set().union(*(d.keys() for d in events))
        schema = {'Event Name','Event Description','Event Start Date','Event Start Time',
                  'Event End Date','Event End Time','Timezone','All Day Event',
                  'Event Venue Name','Event Organizers',
                  'Event Cost','Event Currency Symbol',
                  'Event Category','Event Website'}
        result = schema.issubset(keys)
        self.assertTrue(result)
    
    def test_events_schema(self):
        '''
        Tests if all of the event fields conform in name to the schema.
        '''
        events = schematize_events(page_two_uri_event_items)
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

    def test_events_schema_bool_type(self):
        '''
        Tests if the boolean type event fields are bool
        '''
        booleans = ['All Day Event','Hide from Event Listings','Sticky in Month View',
                    'Event Show Map Link','Event Show Map','Allow Comments',
                    'Allow Trackbacks and Pingbacks']
        events = schematize_events(page_two_uri_event_items)
        vals = []
        for event in events:
            for k in event:
                if k in booleans:
                    val = event[k]
                    vals.append(val)
        result = all([isinstance(x, bool) for x in vals])
        self.assertTrue(result)

    def test_events_schema_string_type(self):
        '''
        Tests if the str and comma delim event field types are strings.
        '''
        comma_delimited = ['Event Venue Name','Event Organizers','Event Category','Event Tags']
        string = ['Event Description','Event Excerpt','Event Name']
        events = schematize_events(page_two_uri_event_items)
        vals = []
        for event in events:
            for k in event:
                if k in string or k in comma_delimited:
                    val = event[k]
                    vals.append(val)
        result = all([isinstance(x, str) for x in vals])
        self.assertTrue(result)
    
    def test_events_schema_currency_symbol_type(self):
        '''
        Tests if the currency symbol is a dollar sign
        '''
        events = schematize_events(page_two_uri_event_items)
        vals = []
        for event in events:
            for k in event:
                if k == 'Event Currency Symbol':
                    vals.append(event[k])
        result = all([x=='$' for x in vals])           
        self.assertTrue(result)
    
    def test_events_schema_event_cost_type(self):
        '''
        Tests if the event cost is a string of digits
        '''
        events = schematize_events(page_two_uri_event_items)
        vals = []
        for event in events:
            for k in event:
                if k == 'Event Cost':
                    val = event[k]
                    vals.append(val)
        #empty strings are "falsy"
        result = all(x.isdigit() or not x for x in vals)
        self.assertTrue(result)

    def test_events_schema_timezone_type(self):
        '''
        Tests if the timezone event field is 'America/New_York'
        '''
        events = schematize_events(page_two_uri_event_items)
        vals = []
        for event in events:
            for k in event:
                if k == 'Timezone':
                    val = event[k]
                    vals.append(val)
        result = all(x == 'America/New_York' for x in vals)
        self.assertTrue(result)

    def test_events_schema_date_type(self):
        '''
        Tests if the event start/end date fields are "%Y-%m-%d" 
        Examples:  '1966-01-01' or '1965-12-31'
        '''
        date = ['Event Start Date', 'Event End Date']
        events = schematize_events(page_two_uri_event_items)
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

    def test_events_schema_time_type(self):
        '''
        Tests if the Event Start Time and Event End Time fields follow
        the "%H:%M:%S" format. Examples: '21:30:00' or '00:50:00'
        '''
        time = ['Event Start Time','Event End Time']
        events = schematize_events(page_two_uri_event_items)
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
            
    def test_events_schema_url_type(self):
        '''
        Tests if the event website and event featured image fields contain strings
        that pass Django's test as urls
        '''
        url = ['Event Website','Event Featured Image']
        events = schematize_events(page_two_uri_event_items)
        vals = []
        for event in events:
            for k in event: 
                if k in url:
                    val = event[k]
                    vals.append(val)
        result = all([re.match(url_regex, x) for x in vals])
        self.assertTrue(result)

    def test_events_schema_currency_position_type(self):
        '''
        Tests if the Event Currency Position is 'prefix', 'suffix', or ''
        '''
        events = schematize_events(page_two_uri_event_items)
        for event in events:
            for k in event: 
                if k == 'Event Currency Position':
                    val = event[k]
                    expected_vals = ['prefix','suffix','']
                    result = val in expected_vals
                    self.assertTrue(result)

    def test_events_schema_phone_type(self):
        '''
        Tests if the phone number string is formatted like:  "+1-326-437-9663"
        '''
        events = schematize_events(page_two_uri_event_items)
        for event in events:
            for k in event: 
                if k == 'Event Phone':
                    val = event[k]
                    result = is_phonenumber_valid(val)
                    self.assertTrue(result)
        
if __name__ == '__main__':
    unittest.main()