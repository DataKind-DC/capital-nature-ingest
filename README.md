[![CircleCI](https://circleci.com/gh/DataKind-DC/capital-nature-ingest/tree/master.svg?style=svg)](https://circleci.com/gh/DataKind-DC/capital-nature-ingest/tree/master) 
# capital-nature-ingest
Webscraping nature-related events from a variety of sources to populate an events calendar on [Capital Nature](http://capitalnature.org/).

## What is Capital Nature?
Capital Nature is a 501c3 nonprofit organization dedicated to bringing nature into the lives of Washington Metro area residents and visitors. They want to highlight on an [events calendar](http://capitalnature.org/events/month/) all the great nature events and experiences happening in the area.

### How do we update the event calendar?
 - For each of the event sources, we use Python (3.6.6) to scrape the events' data and transform it to fit our [schema](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_schema.md).
 - To periodically deploy these Python scripts, we plan to use AWS Lambda.
 - To store our data, we plan to use AWS S3.
 - To track bugs, request new features, or just submit interesting ideas, we use GitHub [issues](https://github.com/DataKind-DC/capital-nature-ingest/issues).

## Getting Started
1. Assuming you've got Python 3.6 and a GitHub account, clone the repo:

```bash
git clone https://github.com/DataKind-DC/capital-nature-ingest.git
```

2. Navigate into the repository you just cloned:

```bash
cd capital-nature-ingest
```

3. Start a virtual environment:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

>You can deactivate the virtual environment with `deactivate`.


4. Get the events:

Before getting the events, you'll need to have a National Park Service (NPS) API key and an Eventbrite API key. 
 - Get one for NPS [here](https://www.nps.gov/subjects/developer/index.htm)
 - Get one for Eventbrite [here](https://www.eventbrite.com/platform/api). For the Eventbrite token, we've found it helpful to follow the instructions in [this blog post](https://www.appypie.com/faqs/how-can-i-get-my-eventbrite-personal-oauth-token-key). After signing up, in the top right dropdown, click on Account Settings > Developer Links sidebar > API Keys then click  on Create API Key or go to this [link](https://www.eventbrite.com/account-settings/apps/new)
 
Once you've got your tokens, add them as environment variables called `NPS_KEY` and `EVENTBRITE_TOKEN`, respectively. Or simply run the script and input them when prompted.

To run the script:

```bash
python get_events.py
```

Running the above will scrape all of the events and output three csv files into a new `data/` dir of the project:
 - `cap-nature-events-<date>.csv` (all of the events)
 - `cap-nature-organizers-<date>.csv` (a list of the event sources, which builds off the previous list each successive time you run this)
 - `cap-nature-venues-<date>.csv` (a list of the event venues, which builds off the previous list each successive time you run this)

## Contributing
If you'd like to lend a hand, hop on over to our [Issues](https://github.com/DataKind-DC/capital-nature-ingest/issues) to see what event sources still need scraping. If you see one that you'd like to tackle, assign yourself to that issue and/or leave a comment saying so. This will let others know that you're working on that event source and that they shouldn't duplicate your efforts.

Once you've found something you want to work on, please read our [contributing guideline](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/CONTRIBUTING.md) for details on how to contribute using git and GitHub. 

## License
[Here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/LICENSE)
