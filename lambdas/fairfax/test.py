import unittest
from unittest.mock import patch, Mock
import httpretty
import requests
from lambda_function import get_event_cost, get_event_date_from_event_website, \
                            get_event_start_date, get_start_times, get_event_description, \
                            get_event_venue, parse_event_website, get_fairfax_events
from test_fixtures import get_event_page_soup

def exceptionCallback(request, uri, headers):
    '''
    Create a callback body that raises an exception when opened. This simulates a bad request.
    '''
    raise requests.ConnectionError('Raising a connection error for the test. You can ignore this!')

class FairfaxTestCase(unittest.TestCase):
    '''
    Test cases for the NPS events
    '''

    def setUp(self):
        self.foo = None

    def tearDown(self):
        self.foo = None

    def test_get_event_cost(self):
        result = get_event_cost(get_event_page_soup())
        expected = '$8.00'
        self.assertEqual(result, expected)


