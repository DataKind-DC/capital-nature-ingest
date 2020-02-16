[![CircleCI](https://circleci.com/gh/DataKind-DC/capital-nature-ingest/tree/master.svg?style=svg)](https://circleci.com/gh/DataKind-DC/capital-nature-ingest/tree/master) 
# capital-nature-ingest

Webscraping outdoorsy events in the Washington DC metro area for an events calendar on [Capital Nature](http://capitalnature.org/).

## What is Capital Nature?

Capital Nature is a 501c3 nonprofit organization dedicated to bringing nature into the lives of DC area residents and visitors. To that end, they maintain an [events calendar](http://capitalnature.org/events/month/) listing all of the area's great nature events.

### How do we update the event calendar?

For each event source identified by Capital Nature, we use Python (3.6.x) to web-scrape events from their websites. As a part of the scrape, we transform the data to fit our [schema](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_schema.md). The scrapers output three separate spreadsheets (csv) that the Capital Nature team then uploads to their Wordpress website.

## Getting Started

You can run the scrapers three different ways:

1. [Locally](#Local-Setup)
    - csv reports are written to `./data`, `./logs` and `./reports`
2. [Locally, with Docker](#Local-Setup-(Docker))
    - good for local testing using an environment that mimics AWS Lambda with option to write results locally
3. [In AWS](#AWS-Setup)
    - csv reports are written to S3

### Local Setup

1. Navigate into the repository:

```bash
cd capital-nature-ingest
```

2. Start a virtual environment:

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

3. Set environment variables:

Before getting the events, you'll need to have a National Park Service (NPS) API key and an Eventbrite API key.
 - Get one for NPS [here](https://www.nps.gov/subjects/developer/index.htm)
 - Get one for Eventbrite [here](https://www.eventbrite.com/platform/api). For the Eventbrite token, we've found it helpful to follow the instructions in [this blog post](https://www.appypie.com/faqs/how-can-i-get-my-eventbrite-personal-oauth-token-key). After signing up, in the top right dropdown, click on Account Settings > Developer Links sidebar > API Keys then click  on Create API Key or go to this [link](https://www.eventbrite.com/account-settings/apps/new)
 
Once you've got your tokens, add them as environment variables called `NPS_KEY` and `EVENTBRITE_TOKEN`. Or simply run the script and input them when prompted.

4. Run the scrapers:

```bash
python get_events.py
```

Read [this](#The-Data) about the script's output.

### Local Setup (Docker)

The Docker environment mimics that of AWS Lambda and is ideal for local testing. Since some of this project's dependencies have to be compiled specifically for AWS, you'll need to run a build sript before building the Docker image and running the container.

1. From the root of the repository, build the project

```bash
build.sh
```

That command zipped the essential components of this project and then combined them with Amazon-Linux-2-compatible versions of numpy and pandas from `layer/aws-lambda-py3.6-pandas-numpy.zip`.

2. Build the image:

```bash
docker build -t scrapers ./lambda-releases
```

3. Run the container:

```bash
docker run --rm -e EVENTBRITE_TOKEN=$EVENTBRITE_TOKEN -e NPS_KEY=$NPS_KEY scrapers
```

If you want to write the results locally, you can mount any combination of `/data`, `/logs`, and `/results` directories to your local filesystem:

```bash
docker run --rm -e EVENTBRITE_TOKEN=$EVENTBRITE_TOKEN -e NPS_KEY=$NPS_KEY -v `pwd`:/var/task/data -v `pwd`:/var/task/logs -v `pwd`:/var/task/reports scrapers
```

The above will write the three data spreadsheets, all of the log files for broken scrapers, and a results spreadsheet to your current working directory.

### AWS Setup

#### Install and Configure the AWS CDK

Follow the instructions [here](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) to install and configure the AWS Cloud Developer Kit (CDK). We're currently using version `1.18.0`.

>Note that you'll need to install node.js as a part of this step if you don't already have it.

If you're new to AWS, you can give your capital nature user account the following AWS-managed IAM policies:

- AWSLambdaFullAccess
- AmazonS3FullAccess
- CloudWatchFullAccess
- AWSCloudFormationFullAccess

Finally, in order to use the CDK, you must specify your account's credentials and AWS Region. There are multiple ways to do this, but the following examples use the `--profile` option with `cdk` commands. This means our credentials and region are specified in `~/.aws/config`.

#### Build the Lambda Asset

If you haven't run this command before (i.e. from the Docker setup), then you need to zip up the relevant components of this project for deployment to AWS Lambda.

```bash
build.sh
```

#### Activate Environment

If you haven't done so already, activate a virtual environment and install the dependencies:

```bash
python -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

#### Deploy

First, run the following command to verify you CDK version:

```bash
cdk --version
```

This should show `1.18.0`.

Now we can deploy/redeploy the app:

```bash
`cdk deploy --profile <your profile name>`
```

After that command has finished, the resources specified in `app.py` have been deployed to the AWS account you configured with the CDK. You can now log into your AWS Console and check out all the stuff.

#### Synthesize Cloudformation Template

You can optionally see the Cloudformation template generated by the CDK. To do so, run `cdk synth`, then check the output file in the `cdk.out/` directory.

#### Cleaning Up

You can destroy the AWS resources created by this app with `cdk destroy --profile <your profile name>`. Note that we've given the S3 Bucket a `removalPolicy` of `cdk.RemovalPolicy.DESTROY` so that it isn't orphaned at the end of this process (you can read more about that [here](https://docs.aws.amazon.com/AmazonS3/latest/user-guide/delete-bucket.html)).

## The Data

After running the scrapers locally, you'll have three csv files in a new `data/` directory (unless you used the Docker approach, in which they'll be wherever you chose to mount the volume):

- `cap-nature-events-<date>.csv` (all of the events)
- `cap-nature-organizers-<date>.csv` (a list of the event sources, which builds off the previous list each successive time you run this)
- `cap-nature-venues-<date>.csv` (a list of the event venues, which builds off the previous list each successive time you run this)

These files are used by the Capital Nature team to update their website.

Two other directories are also created in the process:

- `/reports`
- `/logs`

The `/reports` directory holds spreadsheets that summarize the results of `get_events.py`. There's a row for each event source and columns with data on the number of events scraped, the number of errors encountered, and the event source's status (e.g. "operational") given the presence of errors and/or data. A single report is generated each time you run `get_events.py` and includes the date in the filename to let you connect it to the data files in the `/data` directory. Because of this, if you run `get_events.py` more than once in one day, the previous report is overwritten.

The `/logs` directory naturally contains the logs for each run of `get_events.py`. These files include tracebacks and are useful for developers who want to debug errors. A log file gets genereated for each event source that raises errors. The date is included in the filename, but running `get_events.py` more than once in one day will overwrite the day's previous file.

## Contributing

To track bugs, request new features, or just submit interesting ideas, we use GitHub [issues](https://github.com/DataKind-DC/capital-nature-ingest/issues).

If you'd like to lend a hand, hop on over to our [Issues](https://github.com/DataKind-DC/capital-nature-ingest/issues) to see what event sources still need scraping. If you see one that you'd like to tackle, assign yourself to that issue and/or leave a comment saying so. NOTE: You need to join the DataKindDC GitHub organization in order to assign yourself. If you don't want to join the organization, then just leave a comment and one of us will assign you. Doing this will let others know that you're working on that event source and that they shouldn't duplicate your efforts.

Once you've found something you want to work on, please read our [contributing guideline](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/CONTRIBUTING.md) for details on how to contribute using git and GitHub.

## License

[Here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/LICENSE)
