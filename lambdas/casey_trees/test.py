import unittest
import bs4
import httpretty
import requests
from lambda_function import handle_ans_page
from test_fixtures import event_website_content

class CaseyTreesTestCase(unittest.TestCase):

    def setUp(self):
        self.event_website = 'https://caseytrees.org/event/trees-101-2/'
        self.event_website_content = event_website_content

    def tearDown(self):
        self.event_website = None
        self.event_website_content = None

    @httpretty.activate
    def test_is_event_canceled(self):
        #this is where you mock the request
        httpretty.register_uri(method=httpretty.GET,
                                            uri=self.event_website,
                                            status=200,
                                            body=self.event_website_content)

        r = requests.get(self.event_website)
        content = r.content
        soup = bs4.BeautifulSoup(content, 'html.parser')
        result = handle_ans_page(soup)
        expected = [{'Event Tags': ['tribe-events-category-care', 'tribe-events-category-class'], 'Event Website': 'https://caseytrees.org/event/trees-101-2/', 'Event Name': 'Trees 101', 'Event Cost': '0', 'Event Start Date': '2019-02-09', 'Event Time Zone': 'America/New_York', 'longitude': 'no location', 'Event End Date': '2019-02-09', 'Event Organizer Name(s) or ID(s)': 'Casey Trees', 'Event Venue Name': 'Fort Stanton', 'Event Description': '&lt;p&gt;Do you want to play a greater role in re-treeing D.C.? We need your help to protect and promote trees in our urban forest! Trees 101 provides a foundation in tree anatomy, basic tree identification and an overview of how trees function to provide the benefits we enjoy in the urban forest. The class will [&hellip;]&lt;/p&gt;\\n', 'latitude': 'no location', 'Event Featured Image': 'https://caseytrees.org/wp-content/uploads/2018/12/a1ed661548bf815eae944860bf897fba.jpg', 'Event Currency Symbol': '$', 'Event End Time': '15:00', 'Event Start Time': '10:30'}, {'Event Tags': ['tribe-events-category-advocate', 'tribe-events-category-class'], 'Event Website': 'https://caseytrees.org/event/tree-advocates-meetings-parts-1-2-budget-hearings-discussion-workshop/', 'Event Name': 'Tree Advocates Meetings Parts 1 &#038; 2: Budget Hearings Discussion &#038; Workshop', 'Event Cost': 'Donation', 'Event Start Date': '2019-03-05', 'Event Time Zone': 'America/New_York', 'longitude': 'no location', 'Event End Date': '2019-03-05', 'Event Organizer Name(s) or ID(s)': 'Casey Trees', 'Event Venue Name': 'TBD', 'Event Description': '&lt;p&gt;Please note: This is an invite-only event for Casey Trees Advocates. Volunteers must be able to attend both Part 1: The Discussion and Part 2: The Workshop in order to participate in this tree advocates meeting series. To register, select tickets for both events.\\u00a0 Part 1: The Discussion Tuesday, March 5, 2019 6:30-8 pm Join\\u00a0the [&hellip;]&lt;/p&gt;\\n', 'latitude': 'no location', 'Event Featured Image': 'https://caseytrees.org/wp-content/uploads/2018/12/P1010719.jpg', 'Event Currency Symbol': '$', 'Event End Time': '20:00', 'Event Start Time': '18:30'}]
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
