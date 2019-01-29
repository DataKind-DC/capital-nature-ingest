import unittest
from unittest.mock import patch, Mock
import httpretty
import requests
from lambda_function import get_park_events, get_nps_events, get_specific_event_location, \
                            schematize_nps_event, main
from test_fixtures import get_park_events_expected, nama_events_json, event_page_content, \
                          schematize_nps_event_expected

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

    def test_schematize_nps_event(self):
        result = schematize_nps_event(get_park_events_expected[0])
        expected = schematize_nps_event_expected
        self.assertListEqual(result, expected)

    def test_schematize_nps_event_schema(self):
        event = schematize_nps_event(get_park_events_expected[0])
        keys = set().union(*(d.keys() for d in event))
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
        expected = True
        self.assertEqual(result, expected)
