#!/usr/bin/env python3

from datetime import datetime
import logging
import pandas as pd
import re
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from dateutil import parser
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.setrecursionlimit(30000)
logger = logging.getLogger(__name__)


def retry_session(max_retries=3, backoff_factor=0.5):
    session = requests.Session()
    retry = Retry(total=max_retries, read=max_retries, connect=max_retries,
                  backoff_factor=backoff_factor)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_request(url):
    try:
        r = retry_session().get(url, timeout=1, verify=False)
    except Exception as e:
        msg = f"Exception making GET request to {url}: {e}"
        if url == "https://www.usna.usda.gov/visit/calendar-of-events":
            logger.critical(msg, exc_info=True)
        else:
            logger.e(msg, exc_info=True)
        return
    return r


def get_date(dates_text):
    dates_text = [i for i in dates_text if i != ' ']
    new_list = []
    for i in dates_text:
        i = i.replace('th', '').replace('rd', '').replace('st', '')
        i = i.lower()
        i = i.replace('sunday', '').replace('monday', '').replace('tuesday', '').replace(
            'wednesday', '').replace('thursday', '').replace('friday', '')
        i = i.strip()
        new_list.append(i)
    dates_text = new_list

    dates = []
    for i in dates_text:
        date = datetime.strptime(i, '%B %d %Y').strftime('%Y-%m-%d')
        dates.append(date)

    if len(dates) > 1:
        start_dt = dates[0]
        end_dt = dates[1]
        full_dates = pd.date_range(start_dt, end_dt).tolist()
        date_list = []
        for date in full_dates:
            date = date.strftime('%Y-%m-%d')
            date_list.append(date)
        return date_list
    else:
        return dates


def get_events():
    url = "https://www.usna.usda.gov/visit/calendar-of-events"
    r = get_request(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    articles = soup.find_all('article', {'class': 'cal-brief'})
    events = []
    for article in articles:
        event_item = get_event(article)
        for item in event_item:
            if item is not None:
                if item.get('Event Start Time') != '':
                    events.append(item)
    return events


def get_event(article):
    div = article.find('div', {'class': 'row'})
    a = div.find('a')
    event_href = a.get('href')
    event_website = event_href
    try:
        event_name = div.find('h2').get_text()
    except AttributeError:
        event_name = ''
    try:
        dates_text = div.find('p', {'class': 'full-date'}).get_text().split('-')
        dates = get_date(dates_text)
    except AttributeError:
        dates = ''
    try:
        text_for_time = div.find('p', {'class': 'time'}).get_text()
    except AttributeError:
        text_for_time = ''

    event_start_time = ""
    event_end_time = ""

    if text_for_time != '':
        try:
            event_times = re.findall(r'\s(\d+\:\d+\s?)', text_for_time)
            if len(event_times) > 1:
                start_time = parser.parse(event_times[0])
                event_start_time = datetime.strftime(start_time, '%H:%M:%S')
                end_time = parser.parse(event_times[-1])
                event_end_time = datetime.strftime(end_time, '%H:%M:%S')
            else:
                start_time = parser.parse(event_times[0])
                event_start_time = datetime.strftime(start_time, '%H:%M:%S')

        except AttributeError:
            event_times = text_for_time.split('-')
            if len(event_times) > 1:
                start_time = parser.parse(event_times[0])
                event_start_time = datetime.strftime(start_time, '%H:%M:%S')
                end_time = parser.parse(event_times[-1])
                event_end_time = datetime.strftime(end_time, '%H:%M:%S')
            else:
                start_time = parser.parse(event_times[0])
                event_start_time = datetime.strftime(start_time, '%H:%M:%S')
                event_end_time = event_start_time
    else:
        event_start_time = ''
        event_end_time = ''

    if dates != '':
        multi_events = []
        for idx, val in enumerate(dates):
            event_data = {'Event Website': event_website,
                          'Event Name': event_name,
                          'Event Start Time': event_start_time,
                          'Event End Time': event_end_time,
                          'Event Start Date': dates[idx],
                          'Event End Date': dates[idx],
                          'All Day Event': False,
                          'Timezone': 'America/New_York',
                          'Event Organizers': 'US National Arboretum'}

            event = get_more_info(event_website, event_data)
            multi_events.append(event)
        return multi_events
    else:
        event_data = {'Event Website': event_website,
                      'Event Name': event_name,
                      'Event Start Time': event_start_time,
                      'Event End Time': event_end_time,
                      'Event Start Date': 0,
                      'Event End Date': 0,
                      'All Day Event': False,
                      'Timezone': 'America/New_York',
                      'Event Organizers': 'US National Arboretum'}

        event = get_more_info(event_website, event_data)
        return event


def get_more_info(event_website, event_data):
    r = get_request(event_website)
    soup = BeautifulSoup(r.content, 'html.parser')
    div = soup.find('div', {'class': 'col-sm-9 col-sm-push-3 content'})
    whitelist = ['p']
    text_with_time = [t for t in div.find_all(
        text=True) if t.parent.name in whitelist]
    text_for_time = " ".join(text_with_time)
    if event_data['Event Name'] == '':
        event_name = div.find("h2").get_text()
    else:
        event_name = event_data['Event Name']
    try:
        event_description = div.find('p').get_text()
    except Exception:
        event_description = 'No Description Found'
    # Event Cost
    event_cost_list = re.findall(r'\$(\d+)', text_for_time)
    if event_cost_list == []:
        event_cost = 'Free'
    else:
        event_cost = event_cost_list[0]
    # Event Times
    if event_data['Event Start Time'] == '' and event_data['Event End Time']:
        event_times = re.findall(r'\s(\d+\:\d+\s?)', text_for_time)
        if event_times != '' and len(event_times) > 1:
            start_time = parser.parse(event_times[0])
            event_start_time = datetime.strftime(start_time, '%H:%M:%S')
            end_time = parser.parse(event_times[-1])
            event_end_time = datetime.strftime(end_time, '%H:%M:%S')
        elif event_times != '' and len(event_times) == 1:
            start_time = parser.parse(event_times)
            event_start_time = datetime.strftime(start_time, '%H:%M:%S')
            event_end_time = ''
    else:
        event_start_time = event_data['Event Start Time']
        event_end_time = event_data['Event End Time']
    # Event Date
    if event_data['Event Start Date'] == 0:
        try:
            dates_with_text = div.find('b', text='Date:').next_sibling
            dates_text = str(dates_with_text.encode('utf-8'))
            dates = get_date(dates_text)

        except Exception:
            dates_text = div.find(
                'h3', {'class': 'date'}).get_text().split('-')
            dates = get_date(dates_text)
    else:
        dates = []
    # update dictionaries
    if len(dates) > 0:
        for idx, val in enumerate(dates):
            multi_events = []
            multi_event_data = event_data.update({
                'Event Name': event_name,
                'Event Description': event_description,
                'Event Start Date': dates[idx],
                'Event End Date': dates[idx],
                'Event Start Time': event_start_time,
                'Event End Time': event_end_time,
                'Event Venue Name': '',
                'Event Cost': event_cost,
                'Event Currency Symbol': "$",
                'Event Category': " "
            })
            multi_events.append(multi_event_data)
        return multi_events

    else:
        event_data.update({
            'Event Name': event_name,
            'Event Description': event_description,
            'Event Start Time': event_start_time,
            'Event End Time': event_end_time,
            'Event Venue Name': '',
            'Event Cost': event_cost,
            'Event Currency Symbol': "$",
            'Event Category': " "
        })
        return event_data


def main():
    try:
        events = get_events()
    except Exception as error:
        msg = f"Exception getting event IDs: {error}"
        logger.error(msg, exc_info=True)
    return events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
