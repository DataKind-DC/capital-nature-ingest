import unittest
import bs4
import httpretty
import requests
import json
from lambda_function import handle_ans_page
from test_fixtures import api_content, events_list

class SierraClubDCTestCase(unittest.TestCase):

    def setUp(self):
        self.api = 'https://www.sierraclub.org/sc/proxy?url=https://act.sierraclub.org/events/services/apexrest/eventfeed/ent/6300,5051&_=1548294791086'
        self.api_content = api_content
        self.events_list = events_list
        self.maxDiff = None

    def tearDown(self):
        self.api = None
        self.api_content = None
        self.events_list = None

    @httpretty.activate
    def test_handle_ans_page_success(self):
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.api,
                                            status=200,
                                            body=self.api_content)
        r = requests.get(self.api)
        content = r.content
        page = json.loads(content)
        result = handle_ans_page(page['eventList'])
        expected = self.events_list
        self.assertCountEqual(result, expected)


    @httpretty.activate
    def test_events_schema_required_fields(self):
        '''
        Tests if the required events fields are present.
        '''
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.api,
                                            status=200,
                                            body=self.api_content)
        r = requests.get(self.api)
        content = r.content
        page = json.loads(content)
        events = handle_ans_page(page['eventList'])
        keys = set().union(*(d.keys() for d in events))
        schema = {'Event Name','Event Description','Event Start Date','Event Start Time',
                  'Event End Date','Event End Time','Timezone','All Day Event',
                  'Event Organizers','Event Cost','Event Currency Symbol',
                  'Event Category','Event Website'}
        result = schema.issubset(keys)
        self.assertTrue(result)


    @httpretty.activate
    def test_events_schema(self):
        '''
        Tests if all of the event fields conform in name to the schema.
        '''
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.api,
                                            status=200,
                                            body=self.api_content)
        r = requests.get(self.api)
        content = r.content
        page = json.loads(content)
        events = handle_ans_page(page['eventList'])
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
                                            uri=self.api,
                                            status=200,
                                            body=self.api_content)
        r = requests.get(self.api)
        content = r.content
        page = json.loads(content)
        events = handle_ans_page(page['eventList'])
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
                                            uri=self.api,
                                            status=200,
                                            body=self.api_content)
        r = requests.get(self.api)
        content = r.content
        page = json.loads(content)
        events = handle_ans_page(page['eventList'])
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
                                            uri=self.api,
                                            status=200,
                                            body=self.api_content)
        r = requests.get(self.api)
        content = r.content
        page = json.loads(content)
        events = handle_ans_page(page['eventList'])
        vals = []
        for event in events:
            for k in event:
                if k == 'Event Currency Symbol':
                    vals.append(event[k])
        result = all([x=='$' for x in vals])
        self.assertTrue(result)


    @httpretty.activate
    def test_events_schema_timezone_type(self):
        '''
        Tests if the timezone event field is 'America/New_York'
        '''
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.api,
                                            status=200,
                                            body=self.api_content)
        r = requests.get(self.api)
        content = r.content
        page = json.loads(content)
        events = handle_ans_page(page['eventList'])
        vals = []
        for event in events:
            for k in event:
                if k == 'Timezone':
                    val = event[k]
                    vals.append(val)
        result = all(x == 'America/New_York' for x in vals)
        self.assertTrue(result)


    @httpretty.activate
    def test_events_schema_event_cost_type(self):
        '''
        Tests if the event cost is a string of digits
        '''
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.api,
                                            status=200,
                                            body=self.api_content)
        r = requests.get(self.api)
        content = r.content
        page = json.loads(content)
        events = handle_ans_page(page['eventList'])
        vals = []
        for event in events:
            for k in event:
                if k == 'Event Cost':
                    val = event[k]
                    vals.append(val)
        #empty strings are "falsy"
        result = all(x.isdigit() or not x for x in vals)
        self.assertTrue(result)
