import unittest
from unittest.mock import patch, Mock
import httpretty
import requests
import responses
from bs4 import BeautifulSoup
import sys
from os import path
import re
from datetime import datetime 
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from lambdas.montgomery.lambda_function import get_category_id_map, parse_event_date, get_event_description, \
                            get_event_cost, schematize_event_time, schematize_event_date, \
                            canceled_test, parse_event_website, parse_event_item, no_events_test, \
                            next_page_test, get_category_events, dedupe_events, get_montgomery_events
from fixtures.montgomery_test_fixtures import calendar_page_content, event_page_content, \
                          category_id_map_expected, event_page_content_canceled, parse_event_item_expected, \
                          event_item, calendar_page_no_events_content, calendar_page_next_page_content, \
                          open_house_event, single_event_calendar_page_content, open_house_page_content
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

class MontgomeryTestCase(unittest.TestCase):
    '''
    Test cases for the Montgomery events
    '''

    def setUp(self):
        self.category_id_map_expected = category_id_map_expected
        self.parse_event_item_expected = parse_event_item_expected
        self.calendar_page = 'https://www.montgomeryparks.org/calendar/'
        self.calendar_page_content = calendar_page_content
        self.event_date = 'Fri. January 18th, 2019 10:00am 11:00am'
        self.event_page_content = event_page_content
        self.event_page_content_canceled = event_page_content_canceled
        self.event_website = 'https://www.montgomeryparks.org/events/maple-sugaring-days-147/'
        self.event_website_canceled = 'https://www.montgomeryparks.org/events/bird-blind-birding-5/'
        self.event_item = event_item
        self.calendar_page_no_events_content = calendar_page_no_events_content
        self.calendar_page_next_page_content = calendar_page_next_page_content
        self.open_house_event = open_house_event
        self.single_event_calendar_page_content = single_event_calendar_page_content
        self.open_house_page_content = open_house_page_content
        

    def tearDown(self):
        self.category_id_map_expected = None
        self.parse_event_item_expected = None
        self.calendar_page = None
        self.calendar_page_content = None
        self.event_date = None
        self.event_page_content = None
        self.event_page_content_canceled = None
        self.event_website = None
        self.event_website_canceled = None
        self.event_item = None
        self.calendar_page_no_events_content = None
        self.calendar_page_next_page_content = None
        self.open_house_event = None
        self.single_event_calendar_page_content = None
        self.open_house_page_content = None

    @httpretty.activate
    def test_get_category_id_map(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        result = get_category_id_map()
        expected = self.category_id_map_expected
        self.assertDictEqual(result, expected)

    @httpretty.activate
    def test_get_category_id_map_404(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.calendar_page,
                               status=404,
                               body=exceptionCallback)
        result = get_category_id_map()
        expected = None
        self.assertEqual(result, expected)

    def test_parse_event_date(self):
        start_date, start_time, end_time = parse_event_date(self.event_date)
        result = [start_date, start_time, end_time]
        expected = ['2019-01-18', '10:00:00', '11:00:00']
        self.assertListEqual(result, expected)

    def test_get_event_description(self):
        soup = BeautifulSoup(self.event_page_content, 'html.parser')
        result = get_event_description(soup)
        expected = "February is Maple Sugaring Month at Brookside Nature Center. Every Saturday and Sunday you’ll have an opportunity to experience an American tradition: maple sugaring! Watch the whole maple sugaring process from start to finish. See sap drip from trees and taste it. Watch us boil it down into sweet maple syrup, then sample a tasty treat. Join in the fun and activities and learn something new at this family-friendly program! Space is limited so pre-registration is encouraged."
        self.assertEqual(result, expected)

    def test_get_event_cost(self):
        soup = BeautifulSoup(self.event_page_content, 'html.parser')
        result = get_event_cost(soup)
        expected = '7'
        self.assertEqual(result, expected)

    def test_canceled_test(self):
        soup = BeautifulSoup(self.event_page_content_canceled, 'html.parser')
        result = canceled_test(soup)
        expected = True
        self.assertEqual(result, expected)

    
    #When patching multiple functions, the decorator closest to the function being decorated 
    # is called first, so it will create the first positional argument
    @httpretty.activate
    @patch('lambdas.montgomery.lambda_function.get_event_cost')
    @patch('lambdas.montgomery.lambda_function.get_event_description')
    @patch('lambdas.montgomery.lambda_function.canceled_test')
    def test_parse_event_website(self, mock_canceled_test, mock_get_event_description, mock_get_event_cost):
        mock_canceled_test.return_value = False
        mock_get_event_description.return_value = "February is Maple Sugaring Month at Brookside Nature Center. Every Saturday and Sunday you’ll have an opportunity to experience an American tradition: maple sugaring! Watch the whole maple sugaring process from start to finish. See sap drip from trees and taste it. Watch us boil it down into sweet maple syrup, then sample a tasty treat. Join in the fun and activities and learn something new at this family-friendly program! Space is limited so pre-registration is encouraged."
        mock_get_event_cost.return_value = '7'
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_page_content)
        result = list(parse_event_website(self.event_website))
        expected = [mock_get_event_description.return_value, mock_get_event_cost.return_value]
        self.assertListEqual(result, expected)

    @httpretty.activate
    @patch('lambdas.montgomery.lambda_function.get_event_cost')
    @patch('lambdas.montgomery.lambda_function.get_event_description')
    @patch('lambdas.montgomery.lambda_function.canceled_test')
    def test_parse_event_website_canceled(self, mock_canceled_test, mock_get_event_description, mock_get_event_cost):
        mock_canceled_test.return_value = False
        mock_get_event_description.return_value = None
        mock_get_event_cost.return_value = None
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website_canceled,
                               status=200,
                               body=self.event_page_content_canceled)
        result = list(parse_event_website(self.event_website_canceled))
        expected = [None, None]
        self.assertListEqual(result, expected)

    def test_parse_event_item(self):
        soup = BeautifulSoup(self.event_item, 'html.parser')
        event_item = soup.find('li')
        result = parse_event_item(event_item, 'category')
        expected = self.parse_event_item_expected
        self.assertDictEqual(result, expected)

    def test_no_events_test(self):
        soup = BeautifulSoup(self.calendar_page_no_events_content,'html.parser')
        result = no_events_test(soup)
        expected = True
        self.assertEqual(result, expected)

    def test_no_events_test_false(self):
        soup = BeautifulSoup(self.calendar_page_content,'html.parser')
        result = no_events_test(soup)
        expected = False
        self.assertEqual(result, expected)

    def test_next_page_test(self):
        soup = BeautifulSoup(self.calendar_page_next_page_content, 'html.parser')
        result = next_page_test(soup)
        expected = True
        self.assertEqual(result, expected)

    def test_next_page_test_false(self):
        soup = BeautifulSoup(self.calendar_page_content, 'html.parser')
        result = next_page_test(soup)
        expected = False
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_get_category_events(self):
        httpretty.register_uri(method = httpretty.GET,
                               uri = 'https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method = httpretty.GET,
                               uri = 'https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        result = get_category_events('open house', category_id_map)
        expected = self.open_house_event
        self.assertListEqual(result, expected)

    def test_dedupe_events(self):
        list_of_duplicate_dicts = [{'a':1, 'b':2},
                                   {'a':1, 'b':2},
                                   {'a':1, 'b':2, 'c':3}
                                   ]
        result = len(dedupe_events(list_of_duplicate_dicts))
        expected = len([{'a':1, 'b':2, 'c':3},{'a':1, 'b':2}])
        self.assertEqual(result, expected)

    def test_schematize_event_time(self):
        result = schematize_event_time('9:00pm')
        expected = '21:00:00'
        self.assertEqual(result, expected)

    def test_schematize_event_date(self):
        result = schematize_event_date('Sat. March 23rd, 2019')
        expected = '2019-03-23'
        self.assertEqual(result, expected)
    
    @httpretty.activate
    def test_get_montgomery_events(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        result = get_montgomery_events({'open house': '2901'}, 
                                        event_categories = ['open house'])
        expected = self.open_house_event
        self.assertListEqual(result, expected)

    @httpretty.activate
    def test_events_schema_required_fields(self):
        '''
        Tests if the required events fields are present.
        '''
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
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
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        events = get_category_events('open house', category_id_map)
        for event in events:
            for k in event: 
                if k == 'Event Phone':
                    val = event[k]
                    result = is_phonenumber_valid(val)
                    self.assertTrue(result)
        
if __name__ == '__main__':
    unittest.main()
        