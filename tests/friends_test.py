import os
import unittest
from unittest.mock import patch, Mock
import httpretty
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from events.friends_of_kenilworth_gardens import main, EventbriteIngester
from fixtures.friends_fixtures import api_content, events_list
from utils import EventDateFormatError, EventTimeFormatError, url_regex, \
                  is_phonenumber_valid, exceptionCallback
 
class FRIENDSTestCase(unittest.TestCase):
    '''
    Test cases for the FRIENDS events
    '''

    def setUp(self):
        EVENTBRITE_TOKEN = os.environ['EVENTBRITE_TOKEN']
        self.api = 'https://www.eventbriteapi.com/v3/events/search/?token='+EVENTBRITE_TOKEN+'&organizer.id=8632128868&'
        self.api_content = api_content
        self.events_list = events_list
        self.maxDiff = None

    def tearDown(self):
        self.api = None
        self.api_content = None
        self.events_list = None

    @httpretty.activate
    @patch('events.friends_of_kenilworth_gardens.EventbriteIngester')
    def test_main_success(self, mocked_EventbriteIngester):
        events = main()
        keys = set().union(*(d.keys() for d in events))
        schema = {'Do Not Import', 'Event Name', 'Event Description', 'Event Excerpt',
                  'Event Start Date', 'Event Start Time', 'Event End Date', 'Event End Time',
                  'Timezone', 'All Day Event', 'Hide Event From Event Listings',
                  'Event Sticky in Month View', 'Feature Event', 'Event Venue Name',
                  'Event Organizers', 'Event Show Map Link',
                  'Event Show Map', 'Event Cost', 'Event Currency Symbol',
                  'Event Currency Position', 'Event Category', 'Event Tags',
                  'Event Website', 'Event Featured Image', 'Allow Comments',
                  'Event Allow Trackbacks and Pingbacks'}
        result = keys.issubset(schema)
        self.assertTrue(result)
        
if __name__ == '__main__':
    unittest.main()