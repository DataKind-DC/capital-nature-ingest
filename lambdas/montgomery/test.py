import unittest
from unittest.mock import patch, Mock
import httpretty
import requests
from lambda_function import get_category_id_map, parse_event_date, get_event_description, get_event_cost, \
                            canceled_test, parse_event_website, parse_event_item, no_events_test, \
                            next_page_test, get_category_events, dedupe_events, get_montgomery_events
from test_fixtures import calendar_page_content, event_page_content, event_page_content_canceled, \
                          event_item, calendar_page_no_events_content, calendar_page_next_page_content, \
                          open_house_event, single_event_calendar_page_content, open_house_page_content
from bs4 import BeautifulSoup

def exceptionCallback(request, uri, headers):
    '''
    Create a callback body that raises an exception when opened. This simulates a bad request.
    '''
    raise requests.ConnectionError('Raising a connection error for the test. You can ignore this!')

class FairfaxTestCase(unittest.TestCase):
    '''
    Test cases for the Fairfax events
    '''

    def setUp(self):
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
        expected = {'Archaeology': '1751',
                    'Butterfly Show': '2230',
                    'Camp': '2701',
                    'Clean Up': '2235',
                    'Community Events': '1738',
                    'Community Gardens': '1739',
                    'Community Meeting': '2577',
                    'Earth Month': '3105',
                    'Education': '2239',
                    'Event Center': '3331',
                    'Events': '1740',
                    'Family': '1741',
                    'Featured': '2328',
                    'Festival': '2232',
                    'Free': '1746',
                    'Gardens': '2243',
                    'Golf': '2242',
                    'Hikes': '1733',
                    'Historical/Cultural': '1743',
                    'History': '2240',
                    'History in the Parks': '3215',
                    'History Program': '2234',
                    'Hockey': '1727',
                    'Holiday': '2241',
                    'Ice Skating': '1728',
                    'Kids': '1729',
                    'MLK Day of Service': '2705',
                    'Music': '1744',
                    'Nature': '82',
                    'open house': '2901',
                    'Openings/Dedications': '1753',
                    'Other': '2233',
                    'Park Planning': '2902',
                    'Park Projects': '2916',
                    'Planning Board Meeting': '2751',
                    'Planning Board Worksession': '2756',
                    'pop up': '2569',
                    'Public Hearing': '2754',
                    'Public Meetings': '1750',
                    'Run': '2231',
                    'Special Events': '1730',
                    'Sports': '1731',
                    'Tennis': '1734',
                    'Trail Planning': '2903',
                    'Trail Work': '2706',
                    'Trails': '1735',
                    'Trips': '1736',
                    'Volunteering': '1747',
                    'Weed Warrior': '1748'}
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
        expected = ['Fri. January 18th, 2019', '10:00am', '11:00am']
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
    @patch('lambda_function.get_event_cost')
    @patch('lambda_function.get_event_description')
    @patch('lambda_function.canceled_test')
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
    @patch('lambda_function.get_event_cost')
    @patch('lambda_function.get_event_description')
    @patch('lambda_function.canceled_test')
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
        expected = {'Event Start Date': 'Wed. January 30th, 2019', 'Event Start Time': '10:30am', 'Event End Time': '11:30am', 'Event Website': 'https://www.montgomeryparks.org/events/events/nature-rx-forest-therapy-walks-1-hour-/', 'Event Name': 'Nature Rx: Forest Therapy Walks (1 hour)', 'Event Venue Name': 'Brookside Nature Center', 'Event Cost': '6', 'Event Description': 'Experience the healing and wellness promoting effects of Shinrin-Yoku, the practice of bathing the senses in the atmosphere of the forest. Take a slow and mindful walk with a Forest Therapy guide on a trail at Brookside Nature Center to awaken your senses and reconnect with nature.', 'Event Category': 'category', 'Event Time Zone': 'Eastern Standard Time', 'Event Organizer Name(s) or ID(s)': 'Brookside Nature Center', 'Event Currency Symbol': '$'}
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
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        #using a try block here since httpretty encounters an SSL error
        #so we'll control for it (see https://github.com/gabrielfalcao/HTTPretty/issues/242)
        try:
            result = get_category_events('open house', category_id_map)
            expected = self.open_house_event
            self.assertListEqual(result, expected)
        except requests.exceptions.SSLError:
            result = None
            expected = None
            self.assertEqual(result, expected)

    def test_dedupe_events(self):
        list_of_duplicate_dicts = [{'a':1, 'b':2},
                                   {'a':1, 'b':2},
                                   {'a':1, 'b':2, 'c':3}
                                   ]
        result = len(dedupe_events(list_of_duplicate_dicts))
        expected = len([{'a':1, 'b':2, 'c':3},{'a':1, 'b':2}])
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
        try:
            result = get_montgomery_events({'open house': '2901'}, event_categories = ['open house'])
            expected = self.open_house_event
            self.assertListEqual(result, expected)
        except requests.exceptions.SSLError:
            result = None
            expected = None
            self.assertEqual(result, expected)

    @httpretty.activate
    def test_event_schema(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/calendar/?cat=2901&v=0',
                               status=200,
                               body=self.single_event_calendar_page_content)
        httpretty.register_uri(method=httpretty.GET,
                               uri='https://www.montgomeryparks.org/events/volunteer-fair-for-montgomery-parks-historic-sites/',
                               status=200,
                               body=self.open_house_page_content)
        category_id_map = {'open house': '2901'}
        try:
            events = get_category_events('open house', category_id_map)
            keys = set().union(*(d.keys() for d in events))
            schema = {'Do Not Import','Event Name','Event Description','Event Excerpt',
                    'Event Start Date','Event Start Time','Event End Date','Event End Time',
                    'Event Time Zone','All Day Event','Hide Event From Event Listings',
                    'Event Sticky in Month View','Feature Event','Event Venue Name',
                    'Event Organizer Name(s) or ID(s)','Event Show Map Link',
                    'Event Show Map','Event Cost','Event Currency Symbol',
                    'Event Currency Position','Event Category','Event Tags',
                    'Event Website','Event Featured Image','Event Allow Comments',
                    'Event Allow Trackbacks and Pingbacks'}
            result = keys.issubset(schema)
            self.assertTrue(result)
        except requests.exceptions.SSLError:
            result = None
            expected = None
            self.assertEqual(result, expected)
        