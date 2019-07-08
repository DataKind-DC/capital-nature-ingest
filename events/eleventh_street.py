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
import unicodedata

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
        logger.warning(f'Exception schematizing this date: {event_startTime}', exc_info = True)
        print(event_startTime)
        schematized_event_time = ''
    except ValueError:
        logger.warning(f'Exception schematizing this date: {event_startTime}', exc_info = True)
        schematized_event_time = ''
    
    return schematized_event_time

def get_event_description(event_website_soup):
    try:
        soup_paragraphs = event_website_soup.find('div','tribe-events-single-event-description').find_all('p')
        str_paragraphs = []
        for p in soup_paragraphs:    
            str_paragraphs.append(p.text)
        description = '\n'.join(str_paragraphs)
        
def get_event_organizers(event_website_soup):
    try:

def get_event_venue(event_website_soup):
    try:
        venue_paragraphs = event_website_soup.find('div').find_all('script', 'type':'text/javascript')      
#def schematize_end_date(eventId, event_endTime):
#    try:
#        year = 
#        datetime_obj = datetime.strptime(' '.join(event_endTime.split(' @ ',1)[0], )
#        if date
def main():
    soup = soupify_event_page()
    if not soup:
        sys.exit(1)
    events = soup.find_all('div', class_ = 'tribe_events')
    events_out = [] 
    for e in events:
        event_name = e.select('h3 > a')[0].text
        event_website =  e.select('h3 > a')[0].get("href")
        event_website_soup = soupify_event_website(event_website)
        event_info = eval(e.get('data-tribejson')) # create dict of info
        start_time = schematize_event_time(event_info['startTime'])
        start_date = schematize_event_date(event_info['eventId'], event_info['startTime'])
        end_time = schematize_event_time(event_info['endTime'])
        end_date =  start_date
        
        event_description = get_event_description(event_website_soup)
        event_organizers = get_event_organizers(event_website_soup)
        all_day_event = not(bool(start_time))
        event_venue = get_event_venue(event_website_soup)

        event = {
                 'Event Name': event_name,
                 'Event Website': event_website,
                 'Event Start Date': start_date,
                 'Event Start Time': start_time,
                 'Event End Date': end_date,
                 'Event End Time': end_time,
                 'Event Venue Name': event_venue,
                 'Timezone':'America/New_York',
                 'Event Cost': '',
                 'Event Description': event_description,
                 'Event Category': event_category,
                 'Event Organizers': event_organizers,
                 'Event Currency Symbol':'$',
                 'All Day Event':all_day_event}
        events_out.append(event)



main()