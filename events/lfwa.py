#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 20:49:38 2019
@author: Gene B.
@author: Francisco Vannini
"""

import logging
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import json

logger = logging.getLogger(__name__)

ORG_URL = 'https://www.lfwa.org'


def get_url(url, org_id=None):
    url = f'{url}{org_id}' if org_id else url    
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(
            f"Exception making GET request to {url}: {e}", exc_info=True)
        return
    if not r.ok:
        logger.critical(
            f"Non-200 status of {r.status_code} makign GET request to {url}")
    soup = BeautifulSoup(r.content, 'html.parser')    
    return soup


def handle_img(soup):
    img = soup.find("img", {"class": "thumb-image loaded"})
    img_src = img.get("data-src")
    return img_src


def get_live_events(soup):
    live_events = soup.find(
        "div", 
        {"class": "eventlist eventlist--upcoming"}
    )
    
    event_divs = live_events.find_all(
        "article", 
        {"class": "eventlist-event--upcoming"}
    )
    
    return event_divs


def handle_date(event_soup):
    date = event_soup.find("span", {"id": "Test2:j_id5:j_id24"})
    date = date.text
    date = date.replace(" ", "")
    date_formatted = datetime.strptime(date, "%a%b%d,%Y")
    date = date_formatted.strftime('%Y-%m-%d')
    return date


def handle_start_time(event_soup):
    time_start = event_soup.find("span", {"id": "Test2:j_id5:j_id28"})
    time_start = time_start.text
    time_start = time_start.replace(" ", "")
    time_start_formatted = datetime.strptime(time_start, "%I:%M%p")
    time_start = time_start_formatted.strftime('%H:%M:%S')
    return time_start


def handle_end_time(event_soup):
    time_end = event_soup.find("span", {"id": "Test2:j_id5:j_id32"})
    time_end = time_end.text
    time_end = time_end.replace(" ", "")
    time_end_formatted = datetime.strptime(time_end, "%I:%M%p")
    time_end = time_end_formatted.strftime('%H:%M:%S')
    return time_end


def handle_location(event_soup):
    venue_name = event_soup.find("span", {"id": "Test2:j_id5:j_id36"})
    venue_name = venue_name.text
    return venue_name


def handle_cost(event_soup):
    return "0.00"


def handle_description(event_soup):
    description = str(event_soup.find("span", {"id": "Test2:j_id5:j_id47"}))
    return(description)


def handle_event_name(event_soup):
    event_name = event_soup.find("h1", {"class": "eventlist-title"})
    event_name_string = event_name.text
    return(event_name_string)


def parse_event_divs(event_divs):
    events = []
    for event_div in event_divs:
        event_website = event_div.find(
            "a", 
            {"class": "eventlist-button"}
        ).get("href")
        event_img = event_div.find("img").get("data-src")
        soup_level_two = get_url(ORG_URL + event_website)
        soup_loop = soup_level_two.find("article", {"class": "eventitem"})       
        event_registration_websites = soup_loop.find_all(
            "a", 
            {"class": "sqs-block-button-element"}
        )
        # TODO: Some events DO NOT have a registration link and this
        # link is used to fill out the event information below. It
        # might be the case that the event is valid BUT does not have
        # a registration link. For an example please see :
        # www.lfwa.org/events/free-trees-from-strangling-vines-7kfa7-ws676-7zf9e-nklh7-bst6e
        for a_tag in event_registration_websites:
            soup_level_three = get_url(a_tag.get("href"))
            event_data = {
                'Event Name': handle_event_name(event_div),
                # TODO: Some HTML tags are falling through the cracks
                # in our description string. Eliminate HTML tags
                # without losing the fidelity of the description message.
                'Event Description': handle_description(soup_level_three),
                'Event Start Date': handle_date(soup_level_three),
                'Event Start Time': handle_start_time(soup_level_three),
                'Event End Date': handle_date(soup_level_three),
                'Event End Time': handle_end_time(soup_level_three),
                'All Day Event': "False",
                'Timezone': "America/New_York",
                'Event Venue Name': handle_location(soup_level_three),
                'Event Organizers': 'Little Falls Watershed Alliance',
                'Event Cost': "0.00",
                'Event Currency Symbol': "$",
                # TODO: Get event category from divs with class 
                # "eventlist-cats"
                'Event Category': "",
                'Event Website': ORG_URL + event_website,
                'Event Featured Image': event_img
            }
            events.append(event_data)

    return events


def main():
    soup = get_url(ORG_URL + '/events/')
    event_divs = get_live_events(soup)
    events = parse_event_divs(event_divs)
    return events


if __name__ == '__main__':
    events = main()
    print(json.dumps(events, indent=4, sort_keys=True))