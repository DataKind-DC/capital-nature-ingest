import unittest
from unittest.mock import patch, Mock
import httpretty
import requests
from lambda_function import get_event_cost, get_event_date_from_event_website, \
                            get_event_start_date, get_start_times, get_event_description, \
                            get_event_venue, parse_event_website, get_fairfax_events
from test_fixtures import get_event_page_soup, get_calendar_page_soup, get_start_times_expected, \
                          canceled_page_content, get_fairfax_events_expected

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
        expected = '$8.00'
        self.assertEqual(result, expected)

    def test_get_event_date_from_event_website(self):
        result = get_event_date_from_event_website(self.event_website)
        expected = '01/26/2019'
        self.assertEqual(result, expected)

    def test_get_event_date_from_event_website_no_date(self):
        result = get_event_date_from_event_website(self.event_website_no_date)
        expected = None
        self.assertEqual(result, expected)

    def test_get_event_start_date(self):
        result = get_event_start_date(self.event_page_soup, self.event_website)
        expected = '01/26/2019'
        self.assertEqual(result, expected)

    def test_get_event_start_date_website_no_date(self):
        result = get_event_start_date(self.event_page_soup, self.event_website_no_date)
        expected = '01/26/2019'
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
        expected = ('$8.00',
                    'Hone your fishing skills with this hands-on workshop at Lake Fairfax Park. Topics include tackle, rods and reels. The program runs from 4 to 5 p.m., and the cost is $8 per person. For more information, call 703-471-5414.',
                    'Lake Fairfax',
                    '01/26/2019')
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

    @httpretty.activate
    def test_get_fairfax_events(self):
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
        result = get_fairfax_events()
        expected = get_fairfax_events_expected
        self.assertListEqual(result, expected)


