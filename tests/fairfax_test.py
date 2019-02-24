import unittest
import httpretty
import requests
import re
from datetime import datetime
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from events.fairfax import get_event_cost, get_event_date_from_event_website, \
                           get_event_start_date, get_start_times, get_event_description, \
                           get_event_venue, parse_event_website, schematize_event_date, \
                           schematize_event_time, main
from fixtures.fairfax_test_fixtures import get_event_page_soup, get_calendar_page_soup, \
                                           get_start_times_expected, \
                                           canceled_page_content, main_expected
from utils import EventDateFormatError, EventTimeFormatError, url_regex, \
                  is_phonenumber_valid, exceptionCallback

class FairfaxTestCase(unittest.TestCase):
    '''
    Test cases for the Fairfax events
    '''

    def setUp(self):
        self.event_page_soup, self.event_page_content = get_event_page_soup()
        self.event_website = 'https://www.fairfaxcounty.gov/parks/lake-fairfax/klondike-campfire-cookout/012619'
        self.event_website_no_date = 'https://www.fairfaxcounty.gov/parks/lake-fairfax/klondike-campfire-cookout'
        self.calendar_page_soup, self.calendar_page_content = get_calendar_page_soup()
        self.canceled_page_content = canceled_page_content
        self.calendar_page = 'https://www.fairfaxcounty.gov/parks/park-events-calendar'
        self.event_one_uri = 'https://www.fairfaxcounty.gov/parks/green-spring/wild-women-of-dc/012719'
        self.event_two_uri = 'https://www.fairfaxcounty.gov/parks/green-spring/lecture/gardens-piet-oudolf'

    def tearDown(self):
        self.event_page_soup = None
        self.event_website = None
        self.event_website_no_date = None
        self.calendar_page_soup = None
        self.canceled_page_content = None
        self.event_page_content = None
        self.calendar_page_content = None
        self.calendar_page = None

    def test_get_event_cost(self):
        result = get_event_cost(self.event_page_soup)
        expected = '8'
        self.assertEqual(result, expected)

    def test_get_event_date_from_event_website(self):
        result = get_event_date_from_event_website(self.event_website)
        expected = '2019-01-26'
        self.assertEqual(result, expected)

    def test_get_event_date_from_event_website_no_date(self):
        result = get_event_date_from_event_website(self.event_website_no_date)
        expected = None
        self.assertEqual(result, expected)

    def test_get_event_start_date(self):
        result = get_event_start_date(self.event_page_soup, self.event_website)
        expected = '2019-01-26'
        self.assertEqual(result, expected)

    def test_get_event_start_date_website_no_date(self):
        result = get_event_start_date(self.event_page_soup, self.event_website_no_date)
        expected = '2019-01-26'
        self.assertEqual(result, expected)

    def test_get_start_times(self):
        result = get_start_times(self.calendar_page_soup)
        expected = get_start_times_expected
        self.assertListEqual(result, expected)

    def test_get_event_description(self):
        result = get_event_description(self.event_page_soup)
        expected = 'Hone your fishing skills with this hands-on workshop at Lake Fairfax Park. Topics include tackle, rods and reels. The program runs from 4 to 5 p.m., and the cost is $8 per person. For more information, call 703-471-5414.'
        self.assertEqual(result, expected)

    def test_get_event_venue(self):
        result = get_event_venue(self.event_page_soup)
        expected = 'Lake Fairfax'
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_parse_event_website(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.event_page_content)
        result = parse_event_website(self.event_website)
        expected = ('8',
                    'Hone your fishing skills with this hands-on workshop at Lake Fairfax Park. Topics include tackle, rods and reels. The program runs from 4 to 5 p.m., and the cost is $8 per person. For more information, call 703-471-5414.',
                    'Lake Fairfax',
                    '2019-01-26')
        self.assertTupleEqual(result, expected)

    @httpretty.activate
    def test_parse_event_website_canceled(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=200,
                               body=self.canceled_page_content)
        result = parse_event_website(self.event_website)
        expected = (None, None, None, None)
        self.assertTupleEqual(result, expected)

    @httpretty.activate
    def test_parse_event_website_404(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website,
                               status=404,
                               body=exceptionCallback)
        result = parse_event_website(self.event_website)
        expected = (None, None, None, None)
        self.assertTupleEqual(result, expected)

    def test_schematize_event_date(self):
        result = schematize_event_date('01/27/2019')
        expected = '2019-01-27'
        self.assertEqual(result, expected)

    def test_schematize_event_time(self):
        result = schematize_event_time('1:30PM')
        expected = '13:30:00'
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_main(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
        result = main()
        expected = main_expected
        self.assertListEqual(result, expected)

    @httpretty.activate
    def test_events_schema_required_fields(self):
        '''
        Tests if the required events fields are present.
        '''
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
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
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
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
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
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
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
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
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
        events = main()
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
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
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

    @httpretty.activate
    def test_events_schema_timezone_type(self):
        '''
        Tests if the timezone event field is 'America/New_York'
        '''
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
        events = main()
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
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
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
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
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
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
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
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
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
                               uri=self.calendar_page,
                               status=200,
                               body=self.calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_one_uri,
                               status=200,
                               body=self.event_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_two_uri,
                               status=200,
                               body=self.event_page_content)
        events = main()
        for event in events:
            for k in event: 
                if k == 'Event Phone':
                    val = event[k]
                    result = is_phonenumber_valid(val)
                    self.assertTrue(result)
        
if __name__ == '__main__':
    unittest.main()