import csv
import datetime
import json
import logging
import os
import requests

try:
    # EVENTBRITE_TOKEN = os.environ['EVENTBRITE_TOKEN']
    EVENTBRITE_TOKEN ='TBQNST6U37HN55FFCSQY'
except KeyError:
    EVENTBRITE_TOKEN = input("Enter your Eventbrite API key:")

logger = logging.getLogger(__name__)
api_url_event = "https://www.eventbriteapi.com/v3/events/89082753915/?token=TBQNST6U37HN55FFCSQY"

print(requests.get(api_url_event).json()['name']['text'])

api_url_org = " "

print(requests.get(api_url_org).json()[''])

