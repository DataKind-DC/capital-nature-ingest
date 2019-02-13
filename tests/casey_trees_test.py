import unittest
import bs4
import httpretty
import requests
from unittest.mock import patch, Mock
import sys
from os import path
import re
from datetime import datetime
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from lambdas.casey_trees.lambda_function import handle_ans_page, get_event_description, parse_event_cost
from fixtures.casey_test_fixtures import event_website_content_feb, \
                                         event_website_content_mar, \
                                         event_website_content_trees, \
                                         expected_events_mocked_desc, \
                                         expected_events

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


class CaseyTreesTestCase(unittest.TestCase):

    def setUp(self):
        self.event_website_feb = 'https://caseytrees.org/events/2019-02/'
        self.event_website_mar = 'https://caseytrees.org/events/2019-03/'
        self.event_website_trees = 'https://caseytrees.org/event/trees-101-2/'
        self.event_website_content_feb = event_website_content_feb
        self.event_website_content_mar = event_website_content_mar
        self.event_website_content_trees = event_website_content_trees
        self.expected_events_mocked_desc = expected_events_mocked_desc
        self.expected_events = expected_events
        self.maxDiff = None

    def tearDown(self):
        self.event_website_feb = None
        self.event_website_mar = None
        self.event_website_trees = None
        self.event_website_content_feb = None
        self.event_website_content_mar = None
        self.event_website_content_trees = None
        self.expected_events_mocked_desc = None
        self.expected_events = None

    def test_parse_event_cost_donation(self):
        result = parse_event_cost("Donation")
        expected = "0"
        self.assertEqual(result, expected)

    def test_parse_event_cost(self):
        result = parse_event_cost("The event costs $1.00")
        expected = "1"
        self.assertEqual(result, expected)
    
    @httpretty.activate
    @patch('lambdas.casey_trees.lambda_function.get_event_description')
    def test_handle_ans_page_success(self, mock_get_event_description):
        mock_get_event_description.return_value = 'different function'
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        result = handle_ans_page(soup)
        expected = self.expected_events_mocked_desc
        self.assertCountEqual(result, expected)

    @httpretty.activate
    def test_handle_ans_page_failure(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website_feb,
                               status=200,
                               body="getting the wrong data from fetch page")
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        result = handle_ans_page(soup)
        expected = []
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_get_event_description(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website_trees,
                               status=200,
                               body=self.event_website_content_trees)
        result = get_event_description(self.event_website_trees)
        expected = 'Do you want to play a greater role in re-treeing D.C.? We need your help to protect and promote ' \
                   'trees in our urban forest! Trees 101 provides a foundation in tree anatomy, basic tree ' \
                   'identification and an overview of how trees function to provide the benefits we enjoy in the ' \
                   'urban forest. The class will …'
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_events_schema_required_fields(self):
        '''
        Tests if the required events fields are present.
        '''
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
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
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
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
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
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
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
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
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
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
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
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
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
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
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
        vals = []
        for event in events:
            for k in event:
                if k in date:
                    val = event[k]
                    vals.append(val)
        try:
            result = [datetime.strptime(x, "%Y-%m-%d") for x in vals if x != '']
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
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
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
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
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
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
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
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        events = handle_ans_page(soup)
        for event in events:
            for k in event: 
                if k == 'Event Phone':
                    val = event[k]
                    result = is_phonenumber_valid(val)
                    self.assertTrue(result)
        
if __name__ == '__main__':
    unittest.main()
