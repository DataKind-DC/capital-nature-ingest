import unittest
from unittest.mock import patch, Mock
import httpretty
import requests
from lambda_function import get_arlington_events, html_textraction
from test_fixtures import page_one_uri_json, page_two_uri_json, page_one_uri_event_items, \
                          page_two_uri_event_items

def exceptionCallback(request, uri, headers):
    '''
    Create a callback body that raises an exception when opened. This simulates a bad request.
    '''
    raise requests.ConnectionError('Raising a connection error for the test. You can ignore this!')

class ArlingtonTestCase(unittest.TestCase):
    '''
    Test cases for the Arlington events
    '''

    @classmethod
    def setUpClass(cls):
        cls.foo = None

    @classmethod
    def tearDownClass(cls):
        cls.foo = None

    @httpretty.activate
    def test_get_arlington_events(self):
        page_one_uri = 'https://today-service.arlingtonva.us/api/event/elasticevent?&StartDate=2019-01-25T05:00:00.000Z&EndDate=null&TopicCode=ANIMALS&TopicCode=ENVIRONMENT&ParkingAvailable=false&NearBus=false&NearRail=false&NearBikeShare=false&From=0&Size=5&OrderBy=featured&EndTime=86400000'
        page_two_uri = 'https://today-service.arlingtonva.us/api/event/elasticevent?&StartDate=2019-01-25T05:00:00.000Z&EndDate=null&TopicCode=ANIMALS&TopicCode=ENVIRONMENT&ParkingAvailable=false&NearBus=false&NearRail=false&NearBikeShare=false&From=5&Size=5&OrderBy=featured&EndTime=86400000'
        httpretty.register_uri(httpretty.GET,
                               uri=page_one_uri,
                               body=page_one_uri_json,
                               status=200,
                               content_type = "application/json")

        httpretty.register_uri(httpretty.GET,
                               uri=page_two_uri,
                               body=page_two_uri_json,
                               status=200,
                               content_type = "application/json")
        result = get_arlington_events()
        expected = page_one_uri_event_items + page_two_uri_event_items
        self.assertCountEqual(result, expected)

    def test_html_textraction(self):
        text = '<p>Families age 3 and up. Register children and adults; children must be accompanied by a registered adult. We&#8217;ll use all sorts of cookies, marshmallows and toppings for the most decadent campfire s&#8217;mores ever! For information: 703-228-6535. Meet at Long Branch Nature Center. Registration Required: Resident registration begins at 8:00am on 11/13/2018. Non-resident registration begins at 8:00am on 11/14/2018.</p>\n<p>Activity #:\xa0622959 &#8211; O</p>\n'
        result = html_textraction(text)
        expected = 'Families age 3 and up. Register children and adults; children must be accompanied by a registered adult. We’ll use all sorts of cookies, marshmallows and toppings for the most decadent campfire s’mores ever! For information: 703-228-6535. Meet at Long Branch Nature Center. Registration Required: Resident registration begins at 8:00am on 11/13/2018. Non-resident registration begins at 8:00am on 11/14/2018.'
        self.assertEqual(result, expected)
