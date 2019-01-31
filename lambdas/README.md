# Capital Nature Ingest Lambda Packages

## How to Create a New Package

1. Create a new branch with your name and the Capital Nature source, e.g. `alexidev-casey_trees`
2. Make a new directory in this `lambdas/` directory and name it after the source
3. Copy the contents of the ans directory to your new directory

  Example:
  ```bash
  git checkout -b alexidev-casey_trees
  mkdir casey-trees && cp -r ans/ casey-trees/
  ```

4. Update the `lambda_function.py` code to handle your source. The code in the ans example includes a function `handle_ans_page` which should be replaced with code specific to the source you are working on, but the output object should have the same structure. The output schema we are using at the moment is a list of dicts, with each dict representing an event. The keys in the dict should match the values found [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_schema.md).

  ```json
[
    {
        "Event Cost": "$5 fee due upon registration.",
        "Event Currency Symbol": "$",
        "Event Description": "Families age 3 and up. Register children and adults; children must be accompanied by a registered adult. We\u2019ll use all sorts of cookies, marshmallows and toppings for the most decadent campfire s\u2019mores ever! For information: 703-228-6535. Meet at Long Branch Nature Center. Registration Required: Resident registration begins at 8:00am on 11/13/2018. Non-resident registration begins at 8:00am on 11/14/2018.",
        "Event End Date": "2019-01-26T00:00:00",
        "Event End Time": "19:00:00",
        "Event Name": "Ooey Gooey Campfire",
        "Event Organizer Name(s) or ID(s)": "Long Branch Nature Center at Glencarlyn Park",
        "Event Start Date": "2019-01-26T00:00:00",
        "Event Start Time": "18:00:00",
        "Event Time Zone": "America/New_York",
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
        "Event Organizer Name(s) or ID(s)": "Dawson Terrace",
        "Event Start Date": "2019-01-27T00:00:00",
        "Event Start Time": "10:00:00",
        "Event Time Zone": "America/New_York",
        "Event Venue Name": "Dawson Terrace",
        "Event Website": "https://environment.arlingtonva.us/events/rip-ft-bennett-park-2019-01-27/"
    }
]
  ```

5. Note that if the code requires any additional libraries (right now the ans example only requires beautifulsoup and requests), you should include them in your directory's requirements.txt.

6. You can test the code locally by uncommenting the code at the bottom and updating the `event` object to match your source. E.g. for casey trees:

  ```python
  event = {
    'url': 'https://caseytrees.org/events/',
    'source_name': 'casey-trees'
  }
  ```
 
   ```bash
    python lambda_handler.py
   ```
>You could also do us a huge favor and write some unit tests. :smile: The [HTTPretty](https://httpretty.readthedocs.io/en/latest/) or [responses](https://github.com/getsentry/responses) libraries are handy when it comes to mocking the content returned by a get request.


7. Open a pull request. To build and test a new lambda package I will run `make lambda` in the directory and upload the resulting zip to AWS Lambda for testing.
