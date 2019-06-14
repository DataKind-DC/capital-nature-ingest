# capital-nature-ingest
Webscraping nature-related events from a variety of sources to populate an events calendar on [Capital Nature](http://capitalnature.org/).

## What is Capital Nature?
Capital Nature is a 501c3 nonprofit organization dedicated to bringing nature into the lives of Washington Metro area residents and visitors. They want to highlight on an [events calendar](http://capitalnature.org/events/month/) all the great nature events and experiences happening in the area.

### How do we update the event calendar?
 - For each of the [event sources](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_sources.md), we use Python (3.6.6) to scrape the events' data and transform it to fit our [schema](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_schema.md).
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

3. Start a virtual environment
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

>You can deactivate the virtual environment with:
```bash
deactivate
```

4. Get the events:
Before getting the events, you'll need to have a National Park Service (NPS) API key and an Eventbrite API key. Get one for NPS [here](https://www.nps.gov/subjects/developer/index.htm) and for Eventbrite [here](https://www.eventbrite.com/platform/api). For the Eventbrite token, we've found it helpful to follow the instructions in [this blog post](https://www.appypie.com/faqs/how-can-i-get-my-eventbrite-personal-oauth-token-key) when navigating their site. Once you've got the tokens, add them as environment variables called `NPS_KEY` and `EVENTBRITE_TOKEN`, respectively. Or simply start the script and input them when prompted.

To run the script:

```bash
python get_events.py
```

Running the above will scrape all of the events and output three csvs into the `tmp/` dir of the project:
 - `cap-nature-events-<date>.csv` (all of the events)
 - `cap-nature-organizers-<date>.csv` (a list of the event sources, which builds off the previous list each successive time you run this)
 - `cap-nature-venues-<date>.csv` (a list of the event venues, which builds off the previous list each successive time you run this)

## Contributing
Please read [CONTRIBUTING](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/CONTRIBUTING.md) for details on how to contribute.

## License
[Here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/LICENSE)
