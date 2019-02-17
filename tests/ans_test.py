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
from lambdas.ans.lambda_function import soupify_event_page, soupify_event_website, \
                                        get_event_description, schematize_event_date, \
                                        schematize_event_time, handle_ans_page
from fixtures.ans_test_fixtures import expected_events, get_event_calendar_soup, \
                                       event_website_contents

url_regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class EventDateFormatError(Exception):
   """The Event Start Data and Event End Date fields must be strings following
   the "%Y-%m-%d" format. Examples:  '1966-01-01' or '1965-12-31'
   """
   pass   

class EventTimeFormatError(Exception):
   """The Event Start Time and Event End Time fields must be strings following
   the "%H:%M:%S" format. Examples: '21:30:00' or '00:50:00'
   """
   pass

def is_phonenumber_valid(phone_number):
    '''
    Tests if a phone number is formatted as "+1-326-437-9663"
    
    Parameters:
        phone_number (str):

    Returns:
        True is the number is properly formatted; False otherwise
    '''
    starts_with_plus = phone_number.startswith("+")
    contains_three_dashes = phone_number.count("-")
    all_digits = phone_number.replace("-",'').isdigit()
    result = starts_with_plus and contains_three_dashes and all_digits
    
    return result

def exceptionCallback(request, uri, headers):
    '''
    Create a callback body that raises an exception when opened. This simulates a bad request.
    '''
    raise requests.ConnectionError('Raising a connection error for the test. You can ignore this!')

class ANSTestCase(unittest.TestCase):
    '''
    Test cases for the ANS events
    '''

    def setUp(self):
        self.event_calendar_uri = 'https://anshome.org/events-calendar/'
        self.expected_events = expected_events
        self.event_calendar_soup = get_event_calendar_soup()

    def tearDown(self):
        self.event_calendar_uri = None
        self.expected_events = None
        self.event_calendar_soup = None

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
    
    @httpretty.activate
    def test_soupify_event_website(self):
        httpretty.register_uri(httpretty.GET,
                               uri=self.event_calendar_uri,
                               body=b'soup',
                               status=200,
                               content_type = "application/json")
        result = soupify_event_website(self.event_calendar_uri)
        expected = BeautifulSoup(b'soup','html.parser')
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_soupify_event_website_exception(self):
        httpretty.register_uri(httpretty.GET,
                               uri=self.event_calendar_uri,
                               body=exceptionCallback,
                               status=200,
                               content_type = "application/json")
        result = soupify_event_website(self.event_calendar_uri)
        expected = None
        self.assertEqual(result, expected)
    
    def test_schematize_event_date(self):
        result = schematize_event_date('2019-12-2')
        expected = '2019-12-02'
        self.assertEqual(result, expected)
    
    def test_schematize_event_time(self):
        result = schematize_event_time('1:30 pm')
        expected = '13:30:00'
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_handle_ans_page(self):
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        result = handle_ans_page(self.event_calendar_soup)
        expected = self.expected_events
        self.assertCountEqual(result, expected)
    
    @httpretty.activate
    def test_events_schema_required_fields(self):
        '''
        Tests if the required events fields are present.
        '''
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
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
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
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
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
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
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
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
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
        vals = []
        for event in events:
            for k in event:
                if k == 'Event Currency Symbol':
                    vals.append(event[k])
        result = all([x=='$' for x in vals])           
        self.assertTrue(result)
    
    @httpretty.activate
    def test_events_schema_event_cost_type(self):
        '''
        Tests if the event cost is a string of digits
        '''
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
        vals = []
        for event in events:
            for k in event:
                if k == 'Event Cost':
                    val = event[k]
                    vals.append(val)
        #empty strings are "falsy"
        result = all(x.isdigit() or not x for x in vals)
        self.assertTrue(result)

    @httpretty.activate
    def test_events_schema_timezone_type(self):
        '''
        Tests if the timezone event field is 'America/New_York'
        '''
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
        vals = []
        for event in events:
            for k in event:
                if k == 'Timezone':
                    val = event[k]
                    vals.append(val)
        result = all(x == 'America/New_York' for x in vals)
        self.assertTrue(result)

    @httpretty.activate
    def test_events_schema_date_type(self):
        '''
        Tests if the event start/end date fields are "%Y-%m-%d" 
        Examples:  '1966-01-01' or '1965-12-31'
        '''
        date = ['Event Start Date', 'Event End Date']
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
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
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
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
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
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
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
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
        for event_website_content in event_website_contents:
            event_website = list(event_website_content.keys())[0]
            content = event_website_content[event_website]
            httpretty.register_uri(httpretty.GET,
                                   uri=event_website,
                                   body=content,
                                   status=200)
        events = handle_ans_page(self.event_calendar_soup)
        for event in events:
            for k in event: 
                if k == 'Event Phone':
                    val = event[k]
                    result = is_phonenumber_valid(val)
                    self.assertTrue(result)
        
if __name__ == '__main__':
    unittest.main()