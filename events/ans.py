from datetime import datetime
import json
import logging
import re

import bs4
import requests

logger = logging.getLogger(__name__)

def soupify_page(url = 'https://anshome.org/events-calendar/'):
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(f'Exception making GET to {url}: {e}', exc_info = True)
        return
    content = r.content
    soup = bs4.BeautifulSoup(content, 'html.parser')
    
    return soup

def get_event_data(soup):
    scripts = soup.find_all('script', {'type':'application/ld+json'})
    comma_hugged_by_quotes = re.compile(r'(?<!"),(?!")')
    event_data = []
    for event in scripts:
        e = event.string.replace("\n",'').replace("\t",'').replace("\r",'').replace("@","").strip()
        e = re.sub(r'  +','',e)
        e = re.sub(comma_hugged_by_quotes,"",e)
        e = e.replace('""','","')
        e = json.loads(e)
        event_data.append(e)
    
    return event_data

def get_event_websites(soup):
    events_divs = soup.find_all('div', {'class': 'event'})
    event_websites = [e.find('a',{}).get('href') for e in events_divs]
    
    return event_websites

def schematize_event(event_data, event_websites):
    events = []
    for i,e in enumerate(event_data):
        event_name = e.get('name')
        event_website = event_websites[i]
        start_time, start_date = schematize_event_time(e.get('startDate'))
        end_time, end_date = schematize_event_time(e.get('endDate'))
        event_venue = e.get('location',{}).get('name')
        event_description = e.get('description')
        image = e.get('image','')
        if not all([event_name, event_website, start_date, event_venue, event_description]):
            logger.error(f"Unable to extract all data for ANS event:\n{e}", exc_info=True)
            continue

        event = {'Event Name': event_name,
                 'Event Website': event_website,
                 'Event Start Date': start_date,
                 'Event Start Time': start_time,
                 'Event End Date': end_date,
                 'Event End Time': end_time,
                 'Event Venue Name': event_venue,
                 'Timezone':'America/New_York',
                 'Event Cost': '',
                 'Event Description': event_description,
                 'Event Organizers': 'Audubon Naturalist Society',
                 'Event Currency Symbol':'$',
                 'Event Category':'',
                 'Event Featured Image': image,
                 'All Day Event': False}
        events.append(event)
        
    return events

def schematize_event_time(event_time):
    '''
    Converts a time string like 2019-10-5T08-08-00-00.
    '''
    date, time = event_time.split("T")
    time = time[time.index("-")+1:]

    try:
        time_obj = datetime.strptime(time, "%H-%M-%S")
        schematized_event_time = datetime.strftime(time_obj, "%H:%M:%S")
    except ValueError:
        logger.error(f'Exception schematizing this time: {time}', exc_info=True)
        schematized_event_time = ''
        
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        schematized_event_date = datetime.strftime(date_obj, "%Y-%m-%d")
    except ValueError:
        logger.error(f'Exception schematizing this time: {date}', exc_info=True)
        schematized_event_date = ''
            
    return schematized_event_time, schematized_event_date

def main():
    soup = soupify_page()
    if not soup:
        return []
    event_data = get_event_data(soup)
    event_websites = get_event_websites(soup)
    events = schematize_event(event_data, event_websites)
    
    return events

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
