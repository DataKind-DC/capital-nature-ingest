#!/bin/bash
### Update and set up your instance
sudo yum update -y
sudo yum install git python3 -y
git clone https://github.com/DataKind-DC/capital-nature-ingest.git
cd capital-nature-ingest

### Install pip reqs and set tokens
sudo pip3 install -r requirements.txt
export NPS_KEY="<put NPS key here>"
export EVENTBRITE_TOKEN="<put Eventbrite token here>"

### Run Get Events and send to S3
python3 get_events.py
aws s3 sync data/ s3://<bucket_name>

### Terminate instance
sudo shutdown -h now