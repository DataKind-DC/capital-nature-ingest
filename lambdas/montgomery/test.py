import unittest
from unittest.mock import patch, Mock
import httpretty
import requests
from lambda_function import get_category_id_map, parse_event_date, get_event_description, get_event_cost, \
                            canceled_test
from test_fixtures import calendar_page_content, event_page_content, event_page_canceled
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
        self.event_page_canceled = event_page_canceled

    def tearDown(self):
        self.calendar_page = None
        self.calendar_page_content = None
        self.event_date = None
        self.event_page_content = None
        self.event_page_canceled = None

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
        soup = BeautifulSoup(self.event_page_canceled, 'html.parser')
        result = canceled_test(soup)
        expected = True
        self.assertEqual(result, expected)

    #TODO: patch return values for canceled_test, get_event_description, and get_event_cost. HTTPretty register event page
    def test_parse_event_website(self):
        pass


    

        
