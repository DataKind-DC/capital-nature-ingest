import unittest
import bs4
import requests_mock
import requests
from unittest.mock import patch, Mock
import sys
from os import path
import httpretty
import re
from datetime import datetime
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from events import city_blossoms
from fixtures import city_blossoms_test_fixtures
from utils import EventDateFormatError, EventTimeFormatError, url_regex, \
                  is_phonenumber_valid, exceptionCallback


class CityBlossomsTestCase(unittest.TestCase):

    def setUp(self):
        self.events_data = city_blossoms_test_fixtures.events_data
        self.filter_events_expected = city_blossoms_test_fixtures.filter_events_expected
        self.get_event_desc_content = city_blossoms_test_fixtures.get_event_desc_content
        self.event = city_blossoms_test_fixtures.event
        self.schematize_event_expected = city_blossoms_test_fixtures.schematize_event_expected
        self.events_api_json = city_blossoms_test_fixtures.events_api_json
        self.mock_get_event_data = city_blossoms_test_fixtures.mock_get_event_data
        self.mock_get_event_data_schematized = city_blossoms_test_fixtures.mock_get_event_data_schematized

    def tearDown(self):
        self.events_data = None
        self.filter_events_expected = None
        self.get_event_desc_content = None
        self.event = None
        self.schematize_event_expected = None
        self.events_api_json = None
        self.mock_get_event_data = None
        self.mock_get_event_data_schematized = None

    def test_filter_events(self):
        result = city_blossoms.filter_events(self.events_data)
        expected = self.filter_events_expected
        self.assertEqual(result, expected)

    def test_filter_events_no_events(self):
        result = city_blossoms.filter_events([])
        expected = []
        self.assertEqual(result, expected)

    def test_get_datetime(self):
        result = city_blossoms.get_datetime(1556654400590)
        expected = ('2019-04-30', '16:00:00')
        self.assertEqual(result, expected)

    def test_get_datetime_str(self):
        result = city_blossoms.get_datetime('1556654400590')
        expected = ('2019-04-30', '16:00:00')
        self.assertEqual(result, expected)

    @requests_mock.Mocker()
    def test_get_event_description(self, mock_request):
        event_website = 'http://cityblossoms.org/new-events/2019/2/7/the-food-project-winter-institute'
        mock_request.register_uri('GET',
                                  url = event_website,
                                  text = self.get_event_desc_content,
                                  status_code = 200)
        result = city_blossoms.get_event_description(event_website)
        print(result)
        expected = 'Our Youth Entrepreneurship Cooperative program team and participants will be heading to Boston to attend this exciting event. They will work directly with Food Project’s staff and participants to learn about their unique models.Learn more here: http://thefoodproject.org/institute'
        self.assertEqual(result, expected)

    def test_get_event_categories(self):
        result = city_blossoms.get_event_categories({'tags':[],
                                                     'categories':['cats']})
        expected = 'cats'         
        self.assertEqual(result, expected)

    @requests_mock.Mocker()
    def test_schematize_event(self, mock_request):
        event_website = 'http://cityblossoms.org/new-events/2019/2/7/the-food-project-winter-institute'
        mock_request.register_uri('GET',
                                  url = event_website,
                                  text = self.get_event_desc_content,
                                  status_code = 200)
        result = city_blossoms.schematize_event(self.event)
        expected = self.schematize_event_expected
        self.assertEqual(result, expected)

    def test_get_intervening_days(self):
        result = city_blossoms.get_intervening_days('2019-02-07', '2019-02-08')
        expected = ['2019-02-07', '2019-02-08']
        self.assertEqual(result, expected)
    
    @requests_mock.Mocker()
    def test_get_event_data(self, mock_request):
        jar = requests_mock.CookieJar()
        jar.set('crumb', 'bar', domain='cityblossoms.org')
        mock_request.register_uri('GET',
                                  url = 'http://cityblossoms.org/calendar',
                                  status_code = 200,
                                  cookies = jar)
        month = datetime.now().strftime("%m-%Y")
        url = f'http://cityblossoms.org/api/open/GetItemsByMonth?month={month}&collectionId=55a52dfce4b09a8bb0485083&crumb=bar'
        mock_request.register_uri('GET',
                                  url = url,
                                  status_code = 200,
                                  json = self.events_api_json)
        result = city_blossoms.get_event_data()
        expected = self.events_api_json
        self.assertEqual(result, expected)
    
    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_main(self, mock_get_event_data, mock_filter_events, mock_schematize_event):
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        result = city_blossoms.main()
        expected = self.mock_get_event_data_schematized
        self.assertEqual(result, expected)                    
    
    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_required_fields(self, 
                                           mock_get_event_data, 
                                           mock_filter_events, 
                                           mock_schematize_event):
        '''
        Tests if the required events fields are present.
        '''
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
        keys = set().union(*(d.keys() for d in events))
        schema = {'Event Name','Event Description','Event Start Date','Event Start Time',
                  'Event End Date','Event End Time','Timezone','All Day Event',
                  'Event Venue Name','Event Organizers',
                  'Event Cost','Event Currency Symbol',
                  'Event Category','Event Website'}
        result = schema.issubset(keys)
        self.assertTrue(result)
    
    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema(self, 
                           mock_get_event_data, 
                           mock_filter_events, 
                           mock_schematize_event):
        '''
        Tests if all of the event fields conform in name to the schema.
        '''
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
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

    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_bool_type(self, 
                                     mock_get_event_data, 
                                     mock_filter_events, 
                                     mock_schematize_event):
        '''
        Tests if the boolean type event fields are bool
        '''
        booleans = ['All Day Event','Hide from Event Listings','Sticky in Month View',
                    'Event Show Map Link','Event Show Map','Allow Comments',
                    'Allow Trackbacks and Pingbacks']
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
        vals = []
        for event in events:
            for k in event:
                if k in booleans:
                    val = event[k]
                    vals.append(val)
        result = all([isinstance(x, bool) for x in vals])
        self.assertTrue(result)

    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_string_type(self, 
                                       mock_get_event_data, 
                                       mock_filter_events, 
                                       mock_schematize_event):
        '''
        Tests if the str and comma delim event field types are strings.
        '''
        comma_delimited = ['Event Venue Name','Event Organizers','Event Category','Event Tags']
        string = ['Event Description','Event Excerpt','Event Name']
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
        vals = []
        for event in events:
            for k in event:
                if k in string or k in comma_delimited:
                    val = event[k]
                    vals.append(val)
        result = all([isinstance(x, str) for x in vals])
        self.assertTrue(result)
    
    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_currency_symbol_type(self, 
                                                mock_get_event_data, 
                                                mock_filter_events, 
                                                mock_schematize_event):
        '''
        Tests if the currency symbol is a dollar sign
        '''
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
        vals = []
        for event in events:
            for k in event:
                if k == 'Event Currency Symbol':
                    vals.append(event[k])
        result = all([x=='$' for x in vals])           
        self.assertTrue(result)
    
    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_event_cost_type(self, 
                                           mock_get_event_data, 
                                           mock_filter_events, 
                                           mock_schematize_event):
        '''
        Tests if the event cost is a string of digits
        '''
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
        vals = []
        for event in events:
            for k in event:
                if k == 'Event Cost':
                    val = event[k]
                    vals.append(val)
        #empty strings are "falsy"
        result = all(x.isdigit() or not x for x in vals)
        self.assertTrue(result)

    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_timezone_type(self, 
                                         mock_get_event_data, 
                                         mock_filter_events, 
                                         mock_schematize_event):
        '''
        Tests if the timezone event field is 'America/New_York'
        '''
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
        vals = []
        for event in events:
            for k in event:
                if k == 'Timezone':
                    val = event[k]
                    vals.append(val)
        result = all(x == 'America/New_York' for x in vals)
        self.assertTrue(result)

    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_date_type(self, 
                                     mock_get_event_data, 
                                     mock_filter_events, 
                                     mock_schematize_event):
        '''
        Tests if the event start/end date fields are "%Y-%m-%d" 
        Examples:  '1966-01-01' or '1965-12-31'
        '''
        date = ['Event Start Date', 'Event End Date']
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
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

    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_time_type(self, 
                                     mock_get_event_data, 
                                     mock_filter_events, 
                                     mock_schematize_event):
        '''
        Tests if the Event Start Time and Event End Time fields follow
        the "%H:%M:%S" format. Examples: '21:30:00' or '00:50:00'
        '''
        time = ['Event Start Time','Event End Time']
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
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
            
    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_url_type(self, 
                                    mock_get_event_data, 
                                    mock_filter_events, 
                                    mock_schematize_event):
        '''
        Tests if the event website and event featured image fields contain strings
        that pass Django's test as urls
        '''
        url = ['Event Website','Event Featured Image']
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
        vals = []
        for event in events:
            for k in event: 
                if k in url:
                    val = event[k]
                    vals.append(val)
        result = all([re.match(url_regex, x) for x in vals])
        self.assertTrue(result)

    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_currency_position_type(self, 
                                                  mock_get_event_data, 
                                                  mock_filter_events, 
                                                  mock_schematize_event):
        '''
        Tests if the Event Currency Position is 'prefix', 'suffix', or ''
        '''
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
        for event in events:
            for k in event: 
                if k == 'Event Currency Position':
                    val = event[k]
                    expected_vals = ['prefix','suffix','']
                    result = val in expected_vals
                    self.assertTrue(result)

    @patch('events.city_blossoms.schematize_event')
    @patch('events.city_blossoms.filter_events')
    @patch('events.city_blossoms.get_event_data')
    def test_events_schema_phone_type(self, 
                                      mock_get_event_data, 
                                      mock_filter_events, 
                                      mock_schematize_event):
        '''
        Tests if the phone number string is formatted like:  "+1-326-437-9663"
        '''
        mock_get_event_data.return_value = self.mock_get_event_data
        mock_filter_events.return_value = self.mock_get_event_data
        mock_schematize_event.return_value = self.mock_get_event_data_schematized
        events = city_blossoms.main()
        for event in events:
            for k in event: 
                if k == 'Event Phone':
                    val = event[k]
                    result = is_phonenumber_valid(val)
                    self.assertTrue(result)
                    
if __name__ == '__main__':
    unittest.main()                                    