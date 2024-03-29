#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 20:49:38 2019
@author: Gene B.
@author: Francisco Vannini
"""

from datetime import datetime
import os
from urllib3.util.retry import Retry

from bs4 import BeautifulSoup
from dateutil.parser import isoparse
from ics import Calendar
import pytz
import requests
from requests.adapters import HTTPAdapter

from .utils.log import get_logger

logger = get_logger(os.path.basename(__file__))

ORG_URL = 'https://www.lfwa.org'


def requests_retry_session(retries=3, 
                           backoff_factor=0.5, 
                           status_forcelist=(429, 500, 502, 503, 504), 
                           session=None):
    '''
    Use to create an http(s) requests session that will retry a request.
    '''
    session = session or requests.Session()
    retry = Retry(
        total=retries, 
        read=retries, 
        connect=retries, 
        backoff_factor=backoff_factor, 
        status_forcelist=status_forcelist
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session


def get_url(url, org_id=None):
    url = f'{url}{org_id}' if org_id else url    
    try:
        with requests_retry_session() as session:
            r = session.get(url)
    except Exception as e:
        logger.critical(
            f"Exception making GET request to {url}: {e}", exc_info=True)
        return
    if not r.ok:
        logger.critical(
            f"Non-200 status of {r.status_code} makign GET request to {url}")
        return
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
    try:
        date = date.text
    except AttributeError as e:
        logger.error(f"Exception getting date: {e}", exc_info=True)
        return ''
    date = date.replace(" ", "")
    date_formatted = datetime.strptime(date, "%a%b%d,%Y")
    date = date_formatted.strftime('%Y-%m-%d')
    return date


def handle_start_time(event_soup):
    time_start = event_soup.find("span", {"id": "Test2:j_id5:j_id28"})
    try:
        time_start = time_start.text
    except AttributeError as e:
        logger.error(f"Exception getting star time: {e}", exc_info=True)
        return ''
    time_start = time_start.replace(" ", "")
    time_start_formatted = datetime.strptime(time_start, "%I:%M%p")
    time_start = time_start_formatted.strftime('%H:%M:%S')
    return time_start


def handle_end_time(event_soup):
    time_end = event_soup.find("span", {"id": "Test2:j_id5:j_id32"})
    try:
        time_end = time_end.text
    except AttributeError as e:
        logger.error(f"Exception getting end time: {e}", exc_info=True)
        return ''
    time_end = time_end.replace(" ", "")
    time_end_formatted = datetime.strptime(time_end, "%I:%M%p")
    time_end = time_end_formatted.strftime('%H:%M:%S')
    return time_end


def handle_location(event_soup):
    venue_name = event_soup.find("span", {"id": "Test2:j_id5:j_id36"})
    try:
        venue_name = venue_name.text
    except AttributeError as e:
        logger.error(f"Exception getting venue name: {e}", exc_info=True)
        return ''
    return venue_name


def handle_cost(event_soup):
    return "0.00"


def handle_description(event_soup):
    try:
        description = event_soup.find(
            "span",
            {"id": "Test2:j_id5:j_id47"}
        ).text
        return description
    except AttributeError as e:
        logger.error(f"Exception getting description: {e}", exc_info=True)
        return ''


def handle_event_name(event_soup):
    event_name = event_soup.find("h1", {"class": "eventlist-title"})
    try:
        event_name_string = event_name.text
    except AttributeError as e:
        logger.error(f"Exception getting event name: {e}", exc_info=True)
        return ''
    return event_name_string


def parse_event_divs(event_divs):
    events = []
    for event_div in event_divs:
        event_website = event_div.find(
            "a", 
            {"class": "eventlist-button"}
        ).get("href")
        event_img = event_div.find("img").get("data-src")
        soup_level_two = get_url(ORG_URL + event_website)
        if not soup_level_two:
            continue
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
            if not soup_level_three:
                continue
            description = handle_description(soup_level_three)
            start_date = handle_date(soup_level_three)
            start_time = handle_start_time(soup_level_three)
            end_date = handle_date(soup_level_three)
            end_time = handle_end_time(soup_level_three)
            venue_name = handle_location(soup_level_three)
            if not all([start_date, start_time, end_date, end_time, venue_name]):
                continue
            event_data = {
                'Event Name': handle_event_name(event_div),
                # TODO: Some HTML tags are falling through the cracks
                # in our description string. Eliminate HTML tags
                # without losing the fidelity of the description message.
                'Event Description': description,
                'Event Start Date': start_date,
                'Event Start Time': start_time,
                'Event End Date': end_date,
                'Event End Time': end_time,
                'All Day Event': "False",
                'Timezone': "America/New_York",
                'Event Venue Name': venue_name,
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
        if not event_registration_websites:
            ext = soup_level_two.find(
                "a", 
                {"class": "eventitem-meta-export-ical"}).get("href")
            ics_url = ORG_URL + ext
            with requests_retry_session() as session:
                c = Calendar(session.get(ics_url).text)
            e = list(c.timeline)[0]
            # replace fromisoformat, which is not available in python 3.6
            date_begin = isoparse(str(e.begin))
            date_end = isoparse(str(e.end))
            est = pytz.timezone('US/Eastern')
            date_begin = date_begin.astimezone(est)
            date_end = date_end.astimezone(est)
            event_data = {
                'Event Name': str(e.name),
                # TODO: Some HTML tags are falling through the cracks
                # in our description string. Eliminate HTML tags
                # without losing the fidelity of the description message.
                'Event Description': str(e.name),
                'Event Start Date': str(datetime.date(date_begin)),
                'Event Start Time': str(datetime.time(date_begin)),
                'Event End Date': str(datetime.date(date_end)),
                'Event End Time': str(datetime.time(date_end)),
                'All Day Event': "False",
                'Timezone': "America/New_York",
                'Event Venue Name': "See event website",
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
    if not soup:
        return []
    event_divs = get_live_events(soup)
    events = parse_event_divs(event_divs)
    return events


if __name__ == '__main__':
    events = main()
    print(len(events))
