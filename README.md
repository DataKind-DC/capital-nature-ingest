# capital-nature-ingest
Webscraping nature-related events from a variety of sources to populate an events calendar on [Capital Nature](http://capitalnature.org/).

We use AWS Lambda to periodically scrape events, format them to conform to our schema, convert them to three separate csvs, and then push them to AWS S3.

## What is Capital Nature?
Capital Nature is a 501c3 nonprofit organization dedicated to bringing nature into the lives of Washington Metro area residents and visitors. They want to highlight on an [events calendar](http://capitalnature.org/events/month/) all the great nature events and experiences happening in the area.

## Contributing
Please read [CONTRIBUTING](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/CONTRIBUTING.md) for details on how to contribute.

## License
TBD
