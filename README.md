# capital-nature-ingest
Webscraping nature-related events from a variety of sources to populate an events calendar on [Capital Nature](http://capitalnature.org/).

## What is Capital Nature?
Capital Nature is a 501c3 nonprofit organization dedicated to bringing nature into the lives of Washington Metro area residents and visitors. They want to highlight on an [events calendar](http://capitalnature.org/events/month/) all the great nature events and experiences happening in the area.

### How do we update the event calendar?
 - For each of the [event sources](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_sources.md), we use Python (3.6.6) to scrape the events' data and transform it to fit our [schema](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_schema.md).
 - To periodically deploy these Python scripts, we plan to use AWS Lambda.
 - To store our data, we plan to use AWS S3.
 - To track bugs, request new features, or just submit interesting ideas, we use GitHub [issues](https://github.com/DataKind-DC/capital-nature-ingest/issues).

## Contributing
Please read [CONTRIBUTING](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/CONTRIBUTING.md) for details on how to contribute.

## License
TBD
