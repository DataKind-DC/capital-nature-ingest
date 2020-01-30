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

def parse_event_divs(event_divs):
    events = []
    for event_div in event_divs:
        #get image
        #event name
        #event website
        #venue name
        event_website = event_div.find("a").get("href")
        soup_child = get_url(event_website)
        time = soup_child.find("div", {"class": "event-details__data"})
        time_all = time.find_all("p")
        date = time_all[0].contents[0]
        time_interval = time_all[1].contents[0]
        print(date)
        print(time_interval)
        return date, time_interval

def main():
    soup = get_url('https://www.eventbrite.com/o/', org_id=10605256752)
    event_divs = get_live_events(soup)
    parse_event_divs(event_divs)
    # print(event_divs)    
    return len(event_divs)

if __name__ == '__main__':
    events = main()
    # print(events)