import unittest
import bs4
import httpretty
import requests
from unittest.mock import patch, Mock
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from lambdas.casey_trees.lambda_function import handle_ans_page, get_event_description
from fixtures.casey_test_fixtures import event_website_content_feb, event_website_content_mar, event_website_content_trees

def exceptionCallback(request, uri, headers):
    '''
    Create a callback body that raises an exception when opened. This simulates a bad request.
    '''
    raise requests.ConnectionError('Raising a connection error for the test. You can ignore this!')

class CaseyTreesTestCase(unittest.TestCase):

    def setUp(self):
        self.event_website_feb = 'https://caseytrees.org/events/2019-02/'
        self.event_website_mar = 'https://caseytrees.org/events/2019-03/'
        self.event_website_trees = 'https://caseytrees.org/event/trees-101-2/'
        self.event_website_content_feb = event_website_content_feb
        self.event_website_content_mar = event_website_content_mar
        self.event_website_content_trees = event_website_content_trees
        self.maxDiff = None

    def tearDown(self):
        self.event_website = None
        self.event_website_content = None

    @httpretty.activate
    @patch('lambdas.casey_trees.lambda_function.get_event_description')
    def test_handle_ans_page_success(self, mock_get_event_description):
        mock_get_event_description.return_value = 'different function'
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_feb,
                                            status=200,
                                            body=self.event_website_content_feb)
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website_mar,
                                            status=200,
                                            body=self.event_website_content_mar)


        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        result = handle_ans_page(soup)
        expected = [{'Event Tags': 'care,class',
                     'Event Website': 'https://caseytrees.org/event/trees-101-2/',
                     'Event Name': 'Trees 101', 'Event Cost': '0',
                     'Event Start Date': '2019-02-09',
                     'Event Time Zone': 'America/New_York',
                     'Event End Date': '2019-02-09',
                     'Event Organizer Name(s) or ID(s)': 'Casey Trees',
                     'Event Venue Name': 'Fort Stanton',
                     'Event Description': 'different function',
                     'Event Featured Image': 'https://caseytrees.org/wp-content/uploads/2018/12/a1ed661548bf815eae944860bf897fba.jpg',
                     'Event Currency Symbol': '$',
                     'Event End Time': '15:00',
                     'Event Start Time': '10:30'},
                    {'Event Tags': 'advocate,class',
                     'Event Website': 'https://caseytrees.org/event/tree-advocates-meetings-parts-1-2-budget-hearings-discussion-workshop/',
                     'Event Name': 'Tree Advocates Meetings Parts 1 & 2: Budget Hearings Discussion & Workshop',
                     'Event Cost': 'Donation',
                     'Event Start Date': '2019-03-05',
                     'Event Time Zone': 'America/New_York',
                     'Event End Date': '2019-03-05',
                     'Event Organizer Name(s) or ID(s)': 'Casey Trees',
                     'Event Venue Name': 'TBD',
                     'Event Description': 'different function',
                     'Event Featured Image': 'https://caseytrees.org/wp-content/uploads/2018/12/P1010719.jpg',
                     'Event Currency Symbol': '$',
                     'Event End Time': '20:00',
                     'Event Start Time': '18:30'}]
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_handle_ans_page_failure(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website_feb,
                               status=200,
                               body="getting the wrong data from fetch page")
        r = requests.get(self.event_website_feb)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        result = handle_ans_page(soup)
        expected = []
        self.assertEqual(result, expected)

    @httpretty.activate
    def test_get_event_description(self):
        httpretty.register_uri(method=httpretty.GET,
                               uri=self.event_website_trees,
                               status=200,
                               body=self.event_website_content_trees)
        result = get_event_description(self.event_website_trees)
        expected = 'Do you want to play a greater role in re-treeing D.C.? We need your help to protect and promote ' \
                   'trees in our urban forest! Trees 101 provides a foundation in tree anatomy, basic tree ' \
                   'identification and an overview of how trees function to provide the benefits we enjoy in the ' \
                   'urban forest. The class will …'
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
