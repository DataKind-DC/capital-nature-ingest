import unittest
from unittest.mock import patch, Mock
import bs4
import responses
import requests_mock
import requests
import json
import re
from datetime import datetime
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__))))
from events.tnc import get_api_events, main
from fixtures.tnc_test_fixtures import api_json, main_expected, event_page_content
from utils import EventDateFormatError, EventTimeFormatError, url_regex, \
                  is_phonenumber_valid

class TncTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_main(self, mock_customized_url, mock_request):
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        result = main()
        expected = main_expected
        self.assertEqual(result, expected)

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_main_api_connetion_error(self, mock_customized_url, mock_request):
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  exc = requests.exceptions.ConnectTimeout)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        result = main()
        expected = []
        self.assertEqual(result, expected)

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_main_event_page_conn_error(self, mock_customized_url, mock_request):
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  exc = requests.exceptions.ConnectTimeout)
        result = main()
        expected = []
        self.assertEqual(result, expected)

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_required_fields(self, mock_customized_url, mock_request):
        '''
        Tests if the required events fields are present.
        '''
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        events = main()
        keys = set().union(*(d.keys() for d in events))
        schema = {'Event Name','Event Description','Event Start Date','Event Start Time',
                  'Event End Date','Event End Time','Timezone','All Day Event',
                  'Event Venue Name','Event Organizers',
                  'Event Cost','Event Currency Symbol',
                  'Event Category','Event Website'}
        result = schema.issubset(keys)
        self.assertTrue(result)
    
    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema(self, mock_customized_url, mock_request):
        '''
        Tests if all of the event fields conform in name to the schema.
        '''
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
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

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_bool_type(self, mock_customized_url, mock_request):
        '''
        Tests if the boolean type event fields are bool
        '''
        booleans = ['All Day Event','Hide from Event Listings','Sticky in Month View',
                    'Event Show Map Link','Event Show Map','Allow Comments',
                    'Allow Trackbacks and Pingbacks']
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event:
                if k in booleans:
                    val = event[k]
                    vals.append(val)
        result = all([isinstance(x, bool) for x in vals])
        self.assertTrue(result)

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_string_type(self, mock_customized_url, mock_request):
        '''
        Tests if the str and comma delim event field types are strings.
        '''
        comma_delimited = ['Event Venue Name','Event Organizers','Event Category','Event Tags']
        string = ['Event Description','Event Excerpt','Event Name']
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event:
                if k in string or k in comma_delimited:
                    val = event[k]
                    vals.append(val)
        result = all([isinstance(x, str) for x in vals])
        self.assertTrue(result)
    
    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_currency_symbol_type(self, mock_customized_url, mock_request):
        '''
        Tests if the currency symbol is a dollar sign
        '''
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event:
                if k == 'Event Currency Symbol':
                    vals.append(event[k])
        result = all([x=='$' for x in vals])           
        self.assertTrue(result)
    
    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_event_cost_type(self, mock_customized_url, mock_request):
        '''
        Tests if the event cost is a string of digits
        '''
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event:
                if k == 'Event Cost':
                    val = event[k]
                    vals.append(val)
        #empty strings are "falsy"
        result = all(x.isdigit() or not x for x in vals)
        self.assertTrue(result)

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_timezone_type(self, mock_customized_url, mock_request):
        '''
        Tests if the timezone event field is 'America/New_York'
        '''
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event:
                if k == 'Timezone':
                    val = event[k]
                    vals.append(val)
        result = all(x == 'America/New_York' for x in vals)
        self.assertTrue(result)

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_date_type(self, mock_customized_url, mock_request):
        '''
        Tests if the event start/end date fields are "%Y-%m-%d" 
        Examples:  '1966-01-01' or '1965-12-31'
        '''
        date = ['Event Start Date', 'Event End Date']
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        events = main()
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

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_time_type(self, mock_customized_url, mock_request):
        '''
        Tests if the Event Start Time and Event End Time fields follow
        the "%H:%M:%S" format. Examples: '21:30:00' or '00:50:00'
        '''
        time = ['Event Start Time','Event End Time']
        url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
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
            
    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_url_type(self, mock_customized_url, mock_request):
        '''
        Tests if the event website and event featured image fields contain strings
        that pass Django's test as urls
        '''
        url = ['Event Website','Event Featured Image']
        api_url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = api_url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        events = main()
        vals = []
        for event in events:
            for k in event: 
                if k in url:
                    val = event[k]
                    vals.append(val)
        result = all([re.match(url_regex, x) for x in vals])
        self.assertTrue(result)

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_currency_position_type(self, mock_customized_url, mock_request):
        '''
        Tests if the Event Currency Position is 'prefix', 'suffix', or ''
        '''
        api_url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = api_url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        events = main()
        for event in events:
            for k in event: 
                if k == 'Event Currency Position':
                    val = event[k]
                    expected_vals = ['prefix','suffix','']
                    result = val in expected_vals
                    self.assertTrue(result)

    @patch('events.tnc.customized_url')
    @requests_mock.Mocker()
    def test_events_schema_phone_type(self, mock_customized_url, mock_request):
        '''
        Tests if the phone number string is formatted like:  "+1-326-437-9663"
        '''
        api_url = 'https://www.api.com'
        mock_customized_url.return_value = 'https://www.api.com'
        mock_request.register_uri('GET',
                                  url = api_url,
                                  status_code=200,
                                  json = api_json)
        mock_request.register_uri('GET',
                                  url = 'https://www.nature.org/en-us/get-involved/how-to-help/volunteer-and-attend-events/find-local-events-and-opportunities/fairfax-county-watershed-cleanup/',
                                  status_code=200,
                                  content = event_page_content)
        events = main()
        for event in events:
            for k in event: 
                if k == 'Event Phone':
                    val = event[k]
                    result = is_phonenumber_valid(val)
                    self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
