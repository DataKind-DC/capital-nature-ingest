import unittest
from unittest.mock import patch, Mock
import httpretty
import re
from datetime import datetime
import requests
from lambda_function import get_park_events, get_nps_events, get_specific_event_location, \
                            schematize_nps_event, schematize_time, main
from test_fixtures import get_park_events_expected, nama_events_json, event_page_content, \
                          schematize_nps_event_expected

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

class NPSTestCase(unittest.TestCase):
    '''
    Test cases for the NPS events
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @httpretty.activate
    def test_get_park_events(self):
        uri = "https://developer.nps.gov/api/v1/events?parkCode=nama&limit=1000&api_key=testing123"
        httpretty.register_uri(httpretty.GET,
                               uri=uri,
                               body=nama_events_json,
                               status=200,
                               content_type = "application/json")
        result = get_park_events('nama')
        expected = get_park_events_expected
        for r, e in zip(result, expected):
            self.assertDictEqual(r, e)

    @httpretty.activate
    def test_get_park_events_404(self):
        uri = "https://developer.nps.gov/api/v1/events?parkCode=nama&limit=1000&api_key=testing123"
        httpretty.register_uri(httpretty.GET,
                               uri=uri,
                               body=exceptionCallback,
                               status=404)
        result = get_park_events('nama')
        expected = []
        self.assertListEqual(result, expected)

    @httpretty.activate
    def test_get_nps_events(self):
        uri = "https://developer.nps.gov/api/v1/events?parkCode=nama&limit=1000&api_key=testing123"
        httpretty.register_uri(httpretty.GET,
                               uri=uri,
                               body=nama_events_json,
                               status=200,
                               content_type = "application/json")
        result = get_nps_events(park_codes = ['nama'])
        expected = get_park_events_expected
        for r, e in zip(result, expected):
            self.assertDictEqual(r, e)

    @httpretty.activate
    def test_get_specific_event_location(self):
        uri = 'https://www.nps.gov/planyourvisit/event-details.htm?id=691C8DCE-BFF3-B3A6-3D05AF87066F5FDD'
        httpretty.register_uri(httpretty.GET,
                               uri=uri,
                               body=event_page_content,
                               status=200,
                               content_type = "text/html")
        result = get_specific_event_location('691C8DCE-BFF3-B3A6-3D05AF87066F5FDD')
        expected = 'Lincoln Memorial (Bottom of the Stairs by the Plaza)'
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_get_specific_event_location_404(self):
        uri = 'https://www.nps.gov/planyourvisit/event-details.htm?id=691C8DCE-BFF3-B3A6-3D05AF87066F5FDD'
        httpretty.register_uri(httpretty.GET,
                               uri=uri,
                               body=exceptionCallback,
                               status=404)
        result = get_specific_event_location('691C8DCE-BFF3-B3A6-3D05AF87066F5FDD')
        expected = ''
        self.assertEqual(result, expected)

    def test_schematize_time(self):
        result = schematize_time('10:00 AM')
        expected = '10:00:00'
        self.assertEqual(result, expected)
    
    def test_schematize_nps_event(self):
        result = schematize_nps_event(get_park_events_expected[0])
        expected = schematize_nps_event_expected
        self.assertListEqual(result, expected)

    def test_events_schema_required_fields(self):
        '''
        Tests if the required fields are present
        '''
        event = schematize_nps_event(get_park_events_expected[0])
        keys = set().union(*(d.keys() for d in event))
        schema = {'Event Name','Event Description','Event Start Date','Event Start Time',
                  'Event End Date','Event End Time','Timezone','All Day Event',
                  'Event Venue Name','Event Organizer Name(s) or ID(s)',
                  'Event Cost','Event Currency Symbol',
                  'Event Category','Event Website'}
        result = schema.issubset(keys)
        self.assertTrue(result)

    def test_events_schema(self):
        '''
        Tests if all of the event fields conform in name to the schema.
        '''
        event = schematize_nps_event(get_park_events_expected[0])
        keys = set().union(*(d.keys() for d in event))
        schema = {'Do Not Import','Event Name','Event Description','Event Excerpt',
                  'Event Start Date','Event Start Time','Event End Date','Event End Time',
                  'Timezone','All Day Event','Hide Event From Event Listings',
                  'Event Sticky in Month View','Feature Event','Event Venue Name',
                  'Event Organizer Name(s) or ID(s)','Event Show Map Link',
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
        event = schematize_nps_event(get_park_events_expected[0])
        vals = []
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
        event = schematize_nps_event(get_park_events_expected[0])
        vals = []
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
        event = schematize_nps_event(get_park_events_expected[0])
        for k in event:
            if k == 'Event Currency Symbol':
                result = event[k]
                expected = "$"
                self.assertEqual(result, expected)
    
    def test_events_schema_event_cost_type(self):
        '''
        Tests if the event cost is a string of digits
        '''
        event = schematize_nps_event(get_park_events_expected[0])
        for k in event:
            if k == 'Event Cost':
                val = event[k]
                #empty strings are "falsy"
                result = val.isdigit() or not val
                self.assertTrue(result)

    def test_events_schema_timezone_type(self):
        '''
        Tests if the timezone event field is 'America/New_York'
        '''
        event = schematize_nps_event(get_park_events_expected[0])
        for k in event:
            if k == 'Timezone':
                result = event[k]
                expected = 'America/New_York'
                self.assertEqual(result, expected)

    def test_events_schema_date_type(self):
        '''
        Tests if the event start/end date fields are "%Y-%m-%d" 
        Examples:  '1966-01-01' or '1965-12-31'
        '''
        date = ['Event Start Date', 'Event End Date']
        event = schematize_nps_event(get_park_events_expected[0])
        vals = []
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
        event = schematize_nps_event(get_park_events_expected[0])
        vals = []
        for k in event: 
            if k in time:
                val = event[k]
                vals.append(val)
        try:
            result = [datetime.strptime(x, "%H:%M:%S") for x in vals]
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
        event = schematize_nps_event(get_park_events_expected[0])
        vals = []
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
        event = schematize_nps_event(get_park_events_expected[0])
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
        event = schematize_nps_event(get_park_events_expected[0])
        for k in event: 
            if k == 'Event Phone':
                val = event[k]
                result = is_phonenumber_valid(val)
                self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
