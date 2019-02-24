# Capital Nature Event Scrapers
This directory contains a `.py` file for each [event source](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_sources.md).

## How to Create a New Package
So you've claimed an event source for yourself [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_sources.md) and are ready to write some code. That's great!

Here's what to do (**assuming you've read the contributing guidelines in [CONTRIBUTING](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/CONTRIBUTING.md) and [STYLE GUIDE](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/STYLE-GUIDE.md) and have already forked the repo and made a new feature branch named after the event source you've claimed)**:

1. Make a new file in this `events/` directory and name it after your event source (e.g. `events/your_event_source.py`)

2. Write code to scrape your source's events. Your output needs to be a list of dicts, with each dict representing a single event. The key:value pairs in each event dict should match the schema defined [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_schema.md).

For example:
  ```python
[
    {
        "Event Cost": "5",
        "Event Currency Symbol": "$",
        "Event Description": "This event is awesome.",
        "Event End Date": "2019-01-26",
        "Event End Time": "19:00:00",
        "Event Name": "foo",
        "Event Organizers": "baz",
        "Event Start Date": "2019-01-26",
        "Event Start Time": "18:00:00",
        "Timezone": "America/New_York",
        "Event Venue Name": "fiz",
        "Event Website": "https://foo.bar.com",
        "All Day Event: False
    },
    {
        "Event Cost": "0",
        "Event Currency Symbol": "$",
        "Event Description": "Yet another event",
        "Event End Date": "2019-01-27",
        "Event End Time": "12:00:00",
        "Event Name": "foo",
        "Event Organizers": "bar",
        "Event Start Date": "2019-01-27",
        "Event Start Time": "10:00:00",
        "Timezone": "America/New_York",
        "Event Venue Name": "baz",
        "Event Website": "https://www.foo.com",
        "All Day Event":False
    }
]
  ```

3. If your code requires any additional libraries, you should include them in the project's `requirements.txt`.

4. Once you're able to scrape your events and schematize them, create a `main` function that uses the other function(s) you've written to return your events. Then, at the end of your file, include the following snippet:

```python
if __name__ == '__main__'
    events = main()
```

5. Add some unit/integration tests to the `tests/` directory in the root of this project. At a minimum, you should have a test that asserts the result of your script being equal to what's expected by the schema. This makes it easy for reviewers to verify your code. For example:

```python
import unittest
from lambdas.myevent.lambda_function import main
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

class MyEventsTestCase(unittest.TestCase):
    '''
    Test cases for My Events
    '''
    
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_my_events(self):
        result = main()
        expected = [{
                    "Event Cost": "0",
                    "Event Currency Symbol": "$",
                    "Event Description": "foo",
                    "Event End Date": "2019-01-27",
                    "Event End Time": "12:00:00",
                    "Event Name": "baz",
                    "Event Organizers": "buz",
                    "Event Start Date": "2019-01-27",
                    "Event Start Time": "10:00:00",
                    "Timezone": "America/New_York",
                    "Event Venue Name": "Dawson Terrace",
                    "Event Website": "https://www.fizbuz.com",
                    "All Day Event":False}]
        self.assertCountEqual(result, expected)
        
if __name__ == '__main__':
    unittest.main()
```

Some of the other event files have a lot of other tests that you can adapt to your event source. A best practice is to write these tests first and then write code until all of the tests pass.

>NOTE: For any function(s) that make requests, you should mock the content of a response when calling that function in a test ([HTTPretty](https://httpretty.readthedocs.io/en/latest/) and [responses](https://github.com/getsentry/responses) are handy here). Doing so prevents our tests from relying on the ephemeral content of website, which is beyond our control.

>NOTE: There's a `tests/fixtures/` directory where you can define and then import that mocked content. Doing so makes your tests more readable.

6. When you're ready, open a pull request. When reviewing your PR, we'll want to see:
 - if the test(s) you wrote pass
 - if your code runs locally within a virtual environment (meaning you're requirments have been added to `requirements.txt`)
 - that you've got all of the required fields (you could write a test for this; see `test_events_schema_required_fields` [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/tests/ans_test.py))
 - that your data types are correct (you could write a test for this; see the other tests [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/tests/ans_test.py))
