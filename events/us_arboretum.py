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
import os
from .utils.log import get_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.setrecursionlimit(30000)

logger = get_logger(os.path.basename(__file__))


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
    dates = ''
    if dates_text is not None:
        sw = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        dates_text = [i for i in dates_text if i != ' ']
        dates_text = [i for i in dates_text if i.lower() not in sw]
        new_list = []
        for i in dates_text:
            i = i.replace('th', '').replace('rd', '').replace('st', '')
            i = i.lower()
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
    else:
        return dates


def get_events(soup):
    articles = soup.find_all('article', {'class': 'cal-brief'})
    events = []
    for article in articles:
        event_item = get_event(article)
        for item in event_item:
            if len(item) != 0:
                if isinstance(item, dict):
                    if item.get('Event Start Time') != 0:
                        events.append(item)
    return events


def get_event_name(div):
    try:
        event_name = div.find('h2').get_text()
    except AttributeError:
        event_name = ''
    return event_name


def find_times_text(div):
    wlst = ['p']
    try:
        txt = div.find('p', {'class': 'time'}).get_text()
        return txt
    except Exception:
        try:
            txt = [t for t in div.find_all(text=True) if t.parent.name in wlst]
            txt = " ".join(txt)
            return txt
        except Exception:
            txt = ''
            return txt


def get_description(div):
    try:
        event_description = div.find('p').get_text()
    except Exception:
        event_description = 'No Description Found'
    return event_description


def find_dates_text(div):
    try:
        dates_text = div.find('p', {'class': 'full-date'}).get_text()
        dates_text = dates_text.split('-')
        return dates_text
    except Exception:
        try:
            dates_with_text = div.find('b', text='Date:').next_sibling
            dates_text = str(dates_with_text.encode('utf-8'))
            return dates_text
        except Exception:
            try:
                dates_text = div.find('h3', {'class': 'date'}).get_text()
                dates_text = dates_text.split('-')
                return dates_text
            except Exception:
                pass


def find_event_cost(text_with_time):
    event_cost = ''
    try:
        event_cost_list = re.findall(r'\$(\d+)', text_with_time)
        if event_cost_list == []:
            event_cost = 'Free'
            return event_cost
        else:
            event_cost = event_cost_list[0]
            return event_cost
    except Exception:
        return event_cost
            
            
def get_start_time(text_for_time):
    time = 0
    if text_for_time != '':
        try:
            text_for_time = ''.join(text_for_time)
            event_times = re.findall(r'\d{1,2}\:\d{2}', text_for_time)
            start_time = parser.parse(event_times[0])
            time = datetime.strftime(start_time, '%H:%M:%S')
            return time
        except Exception:
            try:
                event_times = re.findall(r'\d{1,2}\:\d{2}', text_for_time)
                start_time = parser.parse(event_times[0])
                time = datetime.strftime(start_time, '%H:%M:%S')
                return time
            except Exception:
                try:
                    event_times = text_for_time.split('-')
                    start_time = parser.parse(event_times[0])
                    time = datetime.strftime(start_time, '%H:%M:%S')
                    return time
                except Exception:
                    return time
           
    else:
        return time
    

def get_end_time(text_for_time):
    time = 0
    if text_for_time != '':
        try:
            text_for_time = ''.join(text_for_time)
            event_times = re.findall(r'\d{1,2}\:\d{2}', text_for_time)
            end_time = parser.parse(event_times[-1])
            time = datetime.strftime(end_time, '%H:%M:%S')
            return time
        except Exception:
            try:
                event_times = re.findall(r'\d{1,2}\:\d{2}', text_for_time)
                end_time = parser.parse(event_times[-1])
                time = datetime.strftime(end_time, '%H:%M:%S')
                return time
            except Exception:
                try:
                    event_times = text_for_time.split('-')
                    end_time = parser.parse(event_times[-1])
                    time = datetime.strftime(end_time, '%H:%M:%S')
                    return time
                except Exception:
                    return time
    else:
        return time
    
    
def get_event(article):
    div = article.find('div', {'class': 'row'})
    a = div.find('a')
    event_href = a.get('href')
    event_website = event_href
    event_name = get_event_name(div)
    text_with_time = find_times_text(div)
    dates_text = find_dates_text(div)
    dates = get_date(dates_text)
    event_start_time = get_start_time(text_with_time)
    event_end_time = get_end_time(text_with_time)
    if dates != '':
        multi_events = []
        for idx, val in enumerate(dates):
            event_data = {'Event Name': event_name,
                          'Event Website': event_website,
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
        event_data = {'Event Name': event_name,
                      'Event Website': event_website,
                      'Event Start Time': event_start_time,
                      'Event End Time': event_end_time,
                      'Event Start Date': dates,
                      'Event End Date': dates,
                      'All Day Event': False,
                      'Timezone': 'America/New_York',
                      'Event Organizers': 'US National Arboretum'}

        event = get_more_info(event_website, event_data)
        return event


def get_more_info(event_website, event_data):
    r = get_request(event_website)
    soup = BeautifulSoup(r.content, 'html.parser')
    div = soup.find('div', {'class': 'col-sm-9 col-sm-push-3 content'})
    text_with_time = find_times_text(div)
    event_description = get_description(div)
    event_cost = find_event_cost(text_with_time)
    dates_text = find_dates_text(div)
    evnt_start_time = event_data['Event Start Time']
    evnt_end_time = event_data['Event End Time']
    if event_data['Event Start Date'] == '':
        try:
            dates = get_date(dates_text)
        except Exception:
            dates = []
    else:
        dates = []
    if evnt_start_time == 0 and evnt_end_time == 0:
        try:
            evnt_start_time = get_start_time(text_with_time)
            evnt_end_time = get_end_time(text_with_time)
        except Exception:
            pass
    if len(dates) > 0:
        for idx, val in enumerate(dates):
            multi_events = []
            multi_event_data = event_data.update({
                'Event Description': event_description,
                'Event Start Date': dates[idx],
                'Event End Date': dates[idx],
                'Event Start Time': evnt_start_time,
                'Event End Time': evnt_end_time,
                'Event Venue Name': 'US National Arboretum',
                'Event Cost': event_cost,
                'Event Currency Symbol': "$",
                'Event Category': " "})
            multi_events.append(multi_event_data)
        return multi_events
    elif len(dates) == 0 and event_data['Event Start Date'] != 0:
        event_data.update({
            'Event Description': event_description,
            'Event Start Time': evnt_start_time,
            'Event End Time': evnt_end_time,
            'Event Venue Name': 'US National Arboretum',
            'Event Cost': event_cost,
            'Event Currency Symbol': "$",
            'Event Category': " "})
        return event_data
    else:
        pass


def main():
    try:
        events = get_events()
        return events
    except Exception as error:
        msg = f"Exception getting event IDs: {error}"
        logger.error(msg, exc_info=True)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
