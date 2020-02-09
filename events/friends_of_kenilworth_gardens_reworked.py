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
import re
import json

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

def get_eventbrite_url(endpoint, endpoint_params={}, get_params={'token': EVENTBRITE_TOKEN}):
    eventbrite_api_base_url = 'https://www.eventbriteapi.com/v3'
    endpoint = endpoint.format(**endpoint_params)
    get_args = ''.join([key + '=' + str(get_params[key]) + '&' for key in get_params.keys()])
    return eventbrite_api_base_url + endpoint + '?' + get_args

def scrape(event_id, event_cost):
    events_url = get_eventbrite_url('/events/' + str(event_id) +'/',get_params = {'token': EVENTBRITE_TOKEN})
    page = requests.get(events_url).json()

    venue_url = get_eventbrite_url('/venues/' + page["venue_id"],  get_params = {'token': EVENTBRITE_TOKEN})
    venue = requests.get(venue_url).json()

    start = datetime.strptime(page['start']['local'], '%Y-%m-%dT%H:%M:%S')
    end = datetime.strptime(page['end']['local'], '%Y-%m-%dT%H:%M:%S')

    if page["category_id"] is None:
        category = 'none'
    else:
        if page["subcategory_id"] is None:
            category_url = get_eventbrite_url('/categories/' + page["category_id"], get_params={'token': EVENTBRITE_TOKEN})
            category = requests.get(category_url).json()["name"]
        else:
            subcategory_url = get_eventbrite_url("/subcategories/" + page["subcategory_id"], get_params={'token': EVENTBRITE_TOKEN})
            category = requests.get(subcategory_url).json()["name"]
    
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
            'Event Organizers': 'Friends Of Kenilworth Aquatic Gardens',
            'Event Cost': event_cost,
            'Event Currency Symbol': "$",
            'Event Category': category,  # TODO: parse event data for optional category fields if present
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

def get_cost_events(soup):
    cost = soup.find("span", {"class": "list-card__label"}).text
    cost = cost.lower()
    cost = cost.replace("free", "0")
    cost = re.sub('[^\d]+','', cost)
    if cost == "":
        cost = "0"
    return cost

def main():
    events_array = []
    soup = get_url('https://www.eventbrite.com/o/', org_id=EVENTBRITE_ORG_ID)
    event_a_refs = get_live_events(soup)

    for events in event_a_refs:
        cost = get_cost_events(events)
        event_id = events.find("a").get("data-eid")
        events_array.append(scrape(event_id, cost))

    return events_array

if __name__ == '__main__':
    events = main()
    print(json.dumps(events,sort_keys=True,indent=4))
