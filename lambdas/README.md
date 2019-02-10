# Capital Nature Ingest Lambda Packages
We're using AWS Lambda to run the scripts and push the output (csvs) to an S3 bucket.

## How to Create a New Package
So you've claimed an event source for yourself [here](https://docs.google.com/spreadsheets/d/1znSHrheEjqmb6OhhZ0ADse844A0Qp9RhsApczMGWSKk/edit#gid=1708332455) and are ready to write some code. That's great!

Here's what to do (assuming you've followed the directions in [CONTRIBUTING](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/CONTRIBUTING.md) and have already forked the repo and made a new feature branch)

1. Make a new directory in this `lambdas/` directory and name it after the event source (e.g. `lambdas/montgomery/`)
2. Copy the contents of a previously finished directory to your new directory:

  Example:
  ```bash
  mkdir your-event-source && cp -r vnps/ your-event-source/
  ```

3. Update the `lambda_function.py` code to handle your event source. The code in the vnps example includes a function `vnps_handler` which follows [the format that AWS Lambda needs](https://docs.aws.amazon.com/lambda/latest/dg/python-programming-model-handler-types.html).

Within your lambda handler, you should call the function(s) that create your event source's output. That output needs to be a list of dicts, with each dict representing a single event. The key:value pairs in each event dict should match the schema defined [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_schema.md).

For example:
  ```json
[
    {
        "Event Cost": "$5 fee due upon registration.",
        "Event Currency Symbol": "$",
        "Event Description": "Families age 3 and up. Register children and adults; children must be accompanied by a registered adult. We use all sorts of cookies, marshmallows and toppings for the most decadent campfire mores ever! For information: 703-228-6535. Meet at Long Branch Nature Center. Registration Required: Resident registration begins at 8:00am on 11/13/2018. Non-resident registration begins at 8:00am on 11/14/2018.",
        "Event End Date": "2019-01-26T00:00:00",
        "Event End Time": "19:00:00",
        "Event Name": "Ooey Gooey Campfire",
        "Event Organizers": "Long Branch Nature Center at Glencarlyn Park",
        "Event Start Date": "2019-01-26T00:00:00",
        "Event Start Time": "18:00:00",
        "Timezone": "America/New_York",
        "Event Venue Name": "Long Branch Nature Center at Glencarlyn Park",
        "Event Website": "https://parks.arlingtonva.us/events/ooey-gooey-campfire/"
    },
    {
        "Event Cost": "See event website.",
        "Event Currency Symbol": "$",
        "Event Description": "Do you like working outside? Join community volunteers in protecting the local environment from invasive plants. This is a continuing project on the fourth Sunday of each month to reclaim the natural area around Ft. Bennett Park from invasive plants. If you have your own garden gloves and tools, please bring them along. Training and additional tools will be provided. Be sure to come dressed for work, wear long pants, long sleeves, and perhaps a hat. You may also want to bring along a water bottle. These events are for volunteers ages 9 to adult. If you are under 18 years old, a parent or guardian will have to sign our volunteer sign-in sheet before you can participate. Training will be provided at the events. There is no need to RSVP unless you are interested in bringing a group of more than five volunteers. Meet in the parking lot behind Dawson Terrace Community Center.",
        "Event End Date": "2019-01-27T00:00:00",
        "Event End Time": "12:00:00",
        "Event Name": "Ft. Bennett Park Invasive Plant Removal",
        "Event Organizers": "Dawson Terrace",
        "Event Start Date": "2019-01-27T00:00:00",
        "Event Start Time": "10:00:00",
        "Timezone": "America/New_York",
        "Event Venue Name": "Dawson Terrace",
        "Event Website": "https://environment.arlingtonva.us/events/rip-ft-bennett-park-2019-01-27/"
    }
]
  ```

5. Note that if the code requires any additional libraries (the vnps example only requires `beautifulsoup` and `requests`), you should include them in your directory's requirements.txt.

6. You can run the code locally by uncommenting the code at the bottom and updating the `event` object to match your source. E.g. for vnps:

  ```python
  # For local testing (it'll write the csv as vnps-results.csv into your working dir)
  event = {
    'url': 'https://vnps.org',
    'source_name': 'vnps'
  }
  is_local = True
  vnps_handler(event, None)
  ```
  
 ```bash
  python lambda_function.py
 ```

You can then open the output csv to see if the column names match our schema and if the values are of the appropriate type (e.g. event start and end times being formatted in 24hr time as '00:50:00' for 12:50 AM or '21:30:00' for 9:30 PM)
 
>You could also do us a huge favor and go one step further by writing some tests. :smile: The [HTTPretty](https://httpretty.readthedocs.io/en/latest/) and [responses](https://github.com/getsentry/responses) libraries are handy when it comes to mocking the content returned by a GET request. You can check out the vnps directory for an example of a full test suite.

7. When you're ready, open a pull request. To build and test a new lambda package I will run `make lambda` in the directory and upload the resulting zip to AWS Lambda for testing.
