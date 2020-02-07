#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 20:49:38 2019
@author: Scott Mcallister
@author: Francisco Vannini
"""
import logging 
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import logging
import os

import json

logger = logging.getLogger(__name__)

FONA_EVENTBRITE_ORG_ID = 8632128868
# For a local run, be sure to create an env variable with your Eventbrite token
# For example:
# $ export EVENTBRITE_TOKEN=<EVENTBRITE TOKEN Key>

try:
    # EVENTBRITE_TOKEN = os.environ['EVENTBRITE_TOKEN']
    EVENTBRITE_TOKEN = "TBQNST6U37HN55FFCSQY"
except KeyError:
    #if it's not an env var, then we might be testing
    EVENTBRITE_TOKEN = input("Enter your Eventbrite Token Key:")

def get_eventbrite_url(endpoint, endpoint_params={}, get_params={'token': EVENTBRITE_TOKEN}):
    eventbrite_api_base_url = 'https://www.eventbriteapi.com/v3'
    endpoint = endpoint.format(**endpoint_params)
    get_args = ''.join([key + '=' + str(get_params[key]) + '&' for key in get_params.keys()])
    return eventbrite_api_base_url + endpoint + '?' + get_args

def scrape(event_id):
    events_url = get_eventbrite_url('/events/' + str(event_id) +'/',get_params = {'token': EVENTBRITE_TOKEN})
    page = requests.get(events_url).json()

    venue_url = get_eventbrite_url('/venues/' + page["venue_id"],  get_params = {'token': EVENTBRITE_TOKEN})
    venue = requests.get(venue_url).json()

    start = datetime.strptime(page['start']['local'], '%Y-%m-%dT%H:%M:%S')
    end = datetime.strptime(page['end']['local'], '%Y-%m-%dT%H:%M:%S')

    event_data = {
            'Event Name': page['name']['text'],
            'Event Description': "(" + venue["address"]["region"] + ") " + page["summary"],
            'Event Start Date': start.strftime('%Y-%m-%d'),
            'Event Start Time': start.strftime('%H:%M:%S'),
            'Event End Date':end.strftime('%Y-%m-%d'),
            'Event End Time':end.strftime('%H:%M:%S'),
            'All Day Event': "False",
            'Timezone': "America/New_York",
            'Event Venue Name': venue["name"],
            'Event Organizers': 'Friends Of Kenilsworth Gardens',
            'Event Cost': "" # TODO: parse event data for cost data,
            'Event Currency Symbol': "$",
            'Event Category': "",  # TODO: parse event data for optional category fields if present
            'Event Website': page['url'],
            'Event Featured Image': ""
        }
    return event_data
    # print(event_data)
    # print(venue["address"]["latitude"])
    # print(venue["address"]["longitude"])
    # print(venue["address"]["localized_area_display"])

def get_url(url, org_id=None):
    url = f'{url}{org_id}' if org_id else url    
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(f"Exception making GET request to {url}: {e}", exc_info=True)
        return
    if not r.ok:
        logger.critical(f"Non-200 status code of {r.status} makign GET request to {url}")
    soup = BeautifulSoup(r.content, 'html.parser')    
    return soup

def get_live_events(soup):
    live_events = soup.find("article", {"id": "live_events"})
    event_divs = live_events.find_all("div", {"class": "list-card-v2"})
    return event_divs
 
def main():
    events_array = []
    soup = get_url('https://www.eventbrite.com/o/', org_id=FONA_EVENTBRITE_ORG_ID)
    event_a_refs = get_live_events(soup)
    for events in event_a_refs:
        events_array.append(scrape(events.find("a").get("data-eid")))
    return events_array

if __name__ == '__main__':
    events = main()
    print(len(events))