#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 20:49:38 2019
@author: Scott Mcallister
@author: Francisco Vannini
"""
from datetime import datetime
import json
import logging
import os

from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

EVENTBRITE_ORG_ID = 8632128868
# For a local run, be sure to create an env variable with your Eventbrite token
# For example:
# $ export EVENTBRITE_TOKEN=<EVENTBRITE TOKEN Key>

try:
    EVENTBRITE_TOKEN = os.environ['EVENTBRITE_TOKEN']
except KeyError:
    #if it's not an env var, then we might be testing
    EVENTBRITE_TOKEN = input("Enter your Eventbrite Token Key:")

def scrape(event_id):
    page = get(event_id, api_resource='events').json()
    venue = get(page["venue_id"], api_resource='venues').json()

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
            'Event Cost': "", # TODO: parse event data for cost data,
            'Event Currency Symbol': "$",
            'Event Category': "",  # TODO: parse event data for optional category fields if present
            'Event Website': page['url'],
            'Event Featured Image': ""
        }
    return event_data

def get(api_id, api_resource, params={'token': EVENTBRITE_TOKEN}):
    url = f'https://www.eventbrite.com/o/{api_id}' if api_resource == 'o' \
        else f'https://www.eventbriteapi.com/v3/{api_resource}/{api_id}'  
    
    try:
        r = requests.get(url, params=params) if api_resource != 'o' else requests.get(url)
    except Exception as e:
        logger.critical(f"Exception making GET request to {url}: {e}", exc_info=True)
        return
    if not r.ok:
        logger.critical(f"Non-200 status code of {r.status_code} makign GET request to {url}")
      
    return r

def get_live_events(soup):
    live_events = soup.find("article", {"id": "live_events"})
    event_divs = live_events.find_all("div", {"class": "list-card-v2"})
    
    return event_divs
 
def main():
    events_array = []
    r = get(EVENTBRITE_ORG_ID, 'o')
    soup = BeautifulSoup(r.content, 'html.parser')  
    event_a_refs = get_live_events(soup)
    for events in event_a_refs:
        events_array.append(scrape(events.find("a").get("data-eid")))
    
    return events_array

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
