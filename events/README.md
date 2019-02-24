# Capital Nature Ingest Lambda Packages
We're going to use AWS Lambda to run the scripts and push the output (csvs) to an S3 bucket.

## How to Create a New Package
So you've claimed an event source for yourself [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_sources.md) and are ready to write some code. That's great!

Here's what to do (assuming you've read the contributing guidelines in [CONTRIBUTING](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/CONTRIBUTING.md) and have already forked the repo and made a new feature branch named after the event source you've claimed):

1. Make a new directory in this `lambdas/` directory and name it after your event source (e.g. `lambdas/your_event_source/`)
2. Copy the contents of a previously finished directory to your new directory:

  Example:
  ```bash
  cd lambdas/
  mkdir your_event_source && cp -r vnps/ your_event_source/
  ```

3. Update the `lambda_function.py` code to handle your event source. What you want is a `main()` function that contains all of your helper functions. Within your `main()` function, you should call the function(s) that create your event source's output. That output needs to be a list of dicts, with each dict representing a single event. The key:value pairs in each event dict should match the schema defined [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_schema.md).

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

4. Note that if the code requires any additional libraries (the vnps example only requires `beautifulsoup` and `requests`), you should include them in your directory's requirements.txt. Add those requirements to the root requirements.txt file (CircleCI uses that).

5. At the end of your file, include the following snippet:

```python
if __name__ == '__main__'
    events = main()
```
 
6. Once you're confident in the output, add some unit/integration tests to the tests directory. At a minimum, you should have a test that asserts the result of your script being equal to what's expected by the schema. For example:

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

>NOTE: For any functions that make requests, you should mock the content of a response ([HTTPretty](https://httpretty.readthedocs.io/en/latest/) and [responses](https://github.com/getsentry/responses) are handy here). Doing so prevents our tests from relying on the ephemeral content of website, which is beyond our control.

7. When you're ready, open a pull request. When reviewing your PR, we'll want to see:
 - if the tests you wrote pass
 - if your code runs locally, producing a csv
 - that you've got all of the required fields
 - that your data types are correct
