from datetime import date
import json
import logging
import re

import bs4
from dateutil.relativedelta import relativedelta
import requests

logger = logging.getLogger(__name__)


def bs4_page(url):
    """Scrapes url, returns soup"""
    try:
        r_val = requests.get(url)
    except Exception as e:
        msg = f'Exception making GET to {url}: {e}'
        logger.critical(msg, exc_info=True)
        return None
    content = r_val.content
    soup = bs4.BeautifulSoup(content, 'html.parser')
    return soup


def event_details(event):
    """Creates dictionary for each event"""
    event_dict = {}
    event_dict['Event Name'] = event['name']
    event_dict['Event Description'] = event_description(event['url'])
    event_dict['Event Start Date'] = event['startDate'][:10]
    event_dict['Event Start Time'] = event['startDate'][11:19]
    event_dict['Event End Date'] = event['endDate'][:10]
    event_dict['Event End Time'] = event['endDate'][11:19]
    event_dict['All Day Event'] = False
    event_dict['Timezone'] = 'America/New_York'
    event_dict = location(event_dict, event)
    event_dict['Event Organizers'] = 'Loudoun Wildlife Conservancy'
    event_dict['Event Cost'] = fees(event_dict['Event Description'])
    event_dict['Event Currency Symbol'] = '$'
    event_dict['Event Category'] = ''
    event_dict['Event Website'] = event['url']
    event_dict['Event Featured Image'] = event['image']
    return event_dict


def event_description(url):
    """Pulls and cleans full event description from page"""
    soup = bs4_page(url)
    script = soup.find('div',
                       {'class':
                        "tribe-events-single-event-description "
                        "tribe-events-content"})
    desc = script.text
    desc = re.sub(r"\n", '', desc)
    desc = re.sub(r"\xa0", '', desc)
    desc = re.sub(r"Share via:More", '', desc)
    return desc


def fees(event):
    """Checks for fees in description and adds fees to dictionary"""
    if 'Fee:' in event:
        fee_list = re.findall(r"[-+]?\d*\.\d+|\d+", event)
        return str(fee_list[1])
    return str('0')


def month(url):
    """Scrapes events from page and creates dictionary"""
    soup = bs4_page(url)
    scripts = soup.find_all('script', {'type': 'application/ld+json'})[1:]
    events = []
    for tag in scripts:
        event_list = json.loads(tag.string[2:])
        for event in event_list:
            event_dict = event_details(event)
            events.append(event_dict)
    return events


def location(event_dict, event):
    """Checks for location name, latitude, and longitude. Adds
    these to event dictionary"""
    if 'location' in event:
        event_dict['Event Venue Name'] = event['location']['name']
        # if 'geo' in event['location']:
            # event_dict['latitude'] = strevent['location']['geo']['latitude']
            # event_dict['longitude'] = str(
                # event['location']['geo']['longitude'])
            # return event_dict
        # event_dict['latitude'] = 'None listed'
        # event_dict['longitude'] = 'None listed'
        return event_dict
    event_dict['Event Venue Name'] = 'None listed'
    # event_dict['latitude'] = 'None listed'
    # event_dict['longitude'] = 'None listed'
    return event_dict


def clean(events):
    """Sorts events by date and removes duplicates"""
    events.sort(key=lambda x: x['Event Start Date'])
    new_events = [i for n, i in enumerate(events) if i not in events[(n + 1):]]
    return new_events


def get_n_months_out(n=3):
    current_date = date.today()
    dates = []
    for i in range(n):
        dates.append(current_date + relativedelta(months=i + 1))
    dates = [d.strftime("%Y-%m") for d in dates]
    
    return dates


def main():
    """Pulls dictionary of events from January and February 2020,
    sorts events and removes duplicates"""
    url = 'https://loudounwildlife.org/events/'
    events = month(url)
    months = get_n_months_out()
    for m in months:
        events += month(f'https://loudounwildlife.org/events/{m}/')
    events = clean(events)
    
    return events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
