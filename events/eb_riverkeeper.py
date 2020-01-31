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

logger = logging.getLogger(__name__)

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

def handle_time(event_soup):
    time = event_soup.find("div", {"class": "event-details__data"})
    time_all = time.find_all("p")
    date = time_all[0].contents[0]
    # %a, %B %d, %Y
    date_formatted = datetime.strptime(date, "%a, %B %d, %Y")
    time_interval = time_all[1].contents[0].split("–")
    time_start = datetime.strptime(time_interval[0].replace(" ",""), "%I:%M%p")
    time_end = datetime.strptime(time_interval[1].replace(" ","")[:-3],"%I:%M%p")
    return date_formatted,time_start,time_end

def handle_location(event_soup):
    location = event_soup.find_all("div", {"class": "event-details__data"})
    location_detail = location[1].find_all("p")
    location_string = ""
    j = 0
    for i in location_detail:
        print(len(i.contents[0]))
        print(i.contents[0])
        if len(i.contents[0]) > 1:
            if j == 0:
                location_string = i.contents[0]
            else:
                location_string = location_string + "," + i.contents[0]
            j += 1
    location_string = location_string.replace("Washington, DC", "Washington DC")
    return location_string

def handle_cost(event_soup):
    cost = event_soup.find("div", {"data-automation": "micro-ticket-box-price"})
    cost_string = cost.find("div", {"class": "js-display-price"}).contents[0].strip()
    cost_string = "0.00" if cost_string.lower() == 'free' else cost_string
    return cost_string

def handle_description(event_soup):
    description = event_soup.find("div", {"data-automation": "listing-event-description"})
    description_string = description.find("p").contents[0]
    return(description_string)

def handle_event_name(event_soup):
    event_name = event_soup.find("h1", {"data-automation": "listing-title"})
    event_name_string = event_name.contents[0]
    return(event_name_string)

def parse_event_divs(event_divs):
    events = []
    for event_div in event_divs:
        event_website = event_div.find("a").get("href")
        event_img = event_div.find("img").get("src")
        soup_child = get_url(event_website)
        handle_description(soup_child)
        handle_event_name(soup_child)
        handle_cost(soup_child)
        event_data = {
            'Event Name': handle_event_name(soup_child),
            'Event Description': handle_description(soup_child),
            #  TODO: replace newlines with double for WP formatting
            'Event Start Date': handle_time(soup_child)[0].strftime('%Y-%m-%d'),
            'Event Start Time': handle_time(soup_child)[1].strftime('%H:%M:%S'),
            'Event End Date': handle_time(soup_child)[0].strftime('%Y-%m-%d'),
            'Event End Time': handle_time(soup_child)[2].strftime('%H:%M:%S'),
            'All Day Event': "False",
            'Timezone': "America/New_York",
            'Event Venue Name': handle_location(soup_child),
            'Event Organizers': 'Anacostia Riverkeeper',
            'Event Cost': handle_cost(soup_child),
            'Event Currency Symbol': "$",
            # 'Event Category': "",  TODO: parse event data for optional category fields if present
            'Event Website': event_website,
            'Event Featured Image': event_img
        }
        print(event_data)
        events.append(event_data)
    print(events[0])
    return events

def main():
    soup = get_url('https://www.eventbrite.com/o/', org_id=10605256752)
    event_divs = get_live_events(soup)
    events = parse_event_divs(event_divs)
    return events

if __name__ == '__main__':
    events = main()
    print(len(events))