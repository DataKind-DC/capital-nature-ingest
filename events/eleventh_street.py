#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 20:49:38 2019

@author: peterreischer
"""

from datetime import datetime
import sys
import requests
from bs4 import BeautifulSoup
import logging
import re
import math

logger = logging.getLogger(__name__)

def soupify_event_page(url = 'https://bbardc.org/events/'):
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(f'Exception making GET to {url}: {e}', exc_info = True)
        return
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')

    return soup

def soupify_event_website(event_website):
    try:
        r = requests.get(event_website)
    except Exception as e:
        logger.critical(f'Exception making GET to {event_website}: {e}', exc_info = True)
        return
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')

    return soup



def schematize_event_time(event_startTime):
    '''
    Converts a time string like 'May 30 @ 1:30 pm' to 24hr time like '13:30:00'
    '''

    try:
        datetime_obj = datetime.strptime(event_startTime.split(' @ ',1)[1], "%I:%M %p")
        schematized_event_time = datetime.strftime(datetime_obj, "%H:%M:%S")
    except IndexError:
        schematized_event_time = ''
    except ValueError:
        logger.warning(f'Exception schematizing this time: {event_startTime}', exc_info = True)
        schematized_event_time = ''

    return schematized_event_time

def schematize_event_dates(event_id, start_date, end_date):
    '''
    Convert a date string like 'May 30 @ 1:30 PM' to a date like 2019-05-30.
    Checks what year the event is taking place in.

    '''
    start_date_out = ''
    end_date_out = ''
    all_day_event = False
    try:
        start_date = datetime.strptime(start_date.split(' @ ', 1)[0], '%B %d')
        end_date = datetime.strptime(end_date.split(' @ ', 1)[0], '%B %d')
        id_date = datetime.strptime(event_id[5:], '%Y-%m-%d')
        start_date = start_date.replace(year = id_date.year)
        end_date = end_date.replace(year = id_date.year)
        if start_date > end_date:
            start_date = start_date.replace(year = id_date.year - 1)
        if (end_date-start_date).days >= 1:
            all_day_event = True
        start_date_out = datetime.strftime(start_date, '%Y-%m-%d')
        end_date_out = datetime.strftime(end_date, '%Y-%m-%d')
    except IndexError:
        pass
    except ValueError:
        logger.warning(f'Exception schematizing this date: {start_date}', exc_info = True)
        logger.warning(f'Exception schematizing this date: {end_date}', exc_info = True)
    return start_date_out, end_date_out, all_day_event

def get_event_description(event_website_soup, event_name):
    description = ''
    try:
        soup_paragraphs = event_website_soup.find('div', 'tribe-events-single-event-description').find_all('p')
        soup_paragraphs = [i.text for i in soup_paragraphs]
        description = ''.join(soup_paragraphs)
    except:
        logger.warning(f'Exception finding this event description: {event_name}', exc_info = True)
    return description

def get_event_venue(event_website_soup, event_name):
    venue = ''
    try:
        venue = event_website_soup.find('dd', class_ = 'tribe-venue').text
    except:
        logger.warning(f'Exception finding this event venue: {event_name}', exc_info = True)
    return venue.strip()

def get_event_category(event_website_soup, event_name):
    category = ''
    try:
        category = event_website_soup.find('dd', class_ = 'tribe-events-event-categories').text
    except AttributeError:
        #print(event_name)
        category = ''
    except:
        logger.warning(f'Exception finding this event category: {event_name}', exc_info = True)
    return category

def get_event_cost(event_website_soup, event_name):
    cost = ''
    try:
        cost = event_website_soup.find('dd', class_ = 'tribe-events-event-cost').text
        str_prices = re.findall(r"[-+]?\d*\.\d+|\d+", cost)
        float_prices = [float(f) for f in str_prices]
        cost = str(math.ceil(max(float_prices)))
    except AttributeError:
        #print(event_name)
        cost = ''
    except:
        logger.warning(f'Exception finding this event cost: {event_name}', exc_info = True)
    return cost

def main():
    soup = soupify_event_page()
#    if not soup:
#        sys.exit(1)
    events = soup.find_all('div', class_ = 'tribe_events')
    events_out = []

    for e in events:
        event_name = e.select('h3 > a')[0].text
        event_website =  e.select('h3 > a')[0].get("href")
        event_website_soup = soupify_event_website(event_website)
        event_info = eval(e.get('data-tribejson')) # create dict of info
        start_time = schematize_event_time(event_info['startTime'])
        dates = schematize_event_dates(event_info['eventId'], event_info['startTime'], event_info['endTime'])
        end_time = schematize_event_time(event_info['endTime'])
        event_description = get_event_description(event_website_soup, event_name)
        event_organizers = ''
        event_venue = get_event_venue(event_website_soup, event_name)
        event_category = get_event_category(event_website_soup, event_name)
        event_cost = get_event_cost(event_website_soup, event_name)
        event = {
                 'Event Name': event_name,
                 'Event Website': event_website,
                 'Event Start Date': dates[0],
                 'Event Start Time': start_time,
                 'Event End Date': dates[1],
                 'Event End Time': end_time,
                 'Event Venue Name': event_venue,
                 'Timezone':'America/New_York',
                 'Event Cost': event_cost,
                 'Event Description': event_description,
                 'Event Category': event_category,
                 'Event Organizers': event_organizers,
                 'Event Currency Symbol':'$',
                 'All Day Event':dates[2]}
        events_out.append(event)
    
    return events_out

main()
