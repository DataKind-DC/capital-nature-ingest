# Capital Nature Ingest Lambda Packages
We're using AWS Lambda to run the scripts and push the output (csvs) to an S3 bucket.

## How to Create a New Package
So you've claimed an event source for yourself [here](https://docs.google.com/spreadsheets/d/1znSHrheEjqmb6OhhZ0ADse844A0Qp9RhsApczMGWSKk/edit#gid=1708332455) and are ready to write some code. That's great!

Here's what to do (assuming you've followed the directions in [CONTRIBUTING](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/CONTRIBUTING.md) and have already forked the repo and made a new feature branch):

1. Make a new directory in this `lambdas/` directory and name it after your event source (e.g. `lambdas/montgomery/`)
2. Copy the contents of a previously finished directory to your new directory:

  Example:
  ```bash
  mkdir your-event-source && cp -r vnps/ your-event-source/
  ```

3. Update the `lambda_function.py` code to handle your event source. The code in the vnps example includes a function `vnps_handler` which follows [the format that AWS Lambda needs](https://docs.aws.amazon.com/lambda/latest/dg/python-programming-model-handler-types.html).

Within your lambda handler, you should call the function(s) that create your event source's output. That output needs to be a list of dicts, with each dict representing a single event. The key:value pairs in each event dict should match the schema defined [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_schema.md).

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

5. You should structure your code so that uncommenting a few lines and changing the gloal variable `is_local` create a csv locally. You can see an example of this in the vnps module:

  ```python
  # For local testing (it'll write the csv as vnps-results.csv into your working dir)
  event = {
    'url': 'https://vnps.org',
    'source_name': 'vnps'
  }
  is_local = True
  vnps_handler(event, None)
  ```
  
  Then running the following:
  
 ```bash
  python lambda_function.py
 ```
produces a csv of the output.

You can then open the output csv to see if the column names match our schema and if the values are of the appropriate type (e.g. event start and end times being formatted in 24hr time as '00:50:00' for 12:50 AM or '21:30:00' for 9:30 PM)
 
6. Once you're confident in the output, add some unit/integration tests to the tests directory. At a minimum, you should have a test that asserts the result of your script being equal to what's expected by the schema. For example:

```python
import unittest
from lambdas.myevent.lambda_function import get_my_events
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
        result = get_my_events()
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
