from datetime import datetime, timedelta
import logging
import os
import re

import requests
from bs4 import BeautifulSoup

from .utils.log import get_logger

logger = get_logger(os.path.basename(__file__))


def form_url():
    start = datetime.now().strftime("%m-%d-%Y").replace("-", "%2F")
    end = (datetime.now() + timedelta(90))
    end = end.strftime("%m-%d-%Y").replace("-", "%2F")
    
    url = (
        "https://www.novaparks.com/efq/events?"
        f"from[value][date]={start}&"
        f"to[value][date]={end}&"
        "response_type=ajax"
    )
    return url


def scrape(url):
    try:
        r = requests.get(url)
    except Exception as e:
        msg = f"Exception making GET request to {url}: {e}"
        logger.critical(msg, exc_info=True)
        return
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    
    event_divs = soup.find_all(
        'div',
        {'class': 'layout layout-one-third-two-thirds'}
    )
    
    return event_divs


def get_event_cost(event_description):
    currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
    
    event_cost = re.findall(currency_re, event_description)

    if len(event_cost) > 0:
        event_cost = event_cost[0].split(".")[0].replace("$", '')
        event_cost = ''.join(s for s in event_cost if s.isdigit())
        return event_cost
    return ''


def get_event_data(event_div):
    href = event_div.find('a').get('href')
    event_name = event_div.find('h3', {'class': 'field-content'}).text
    event_description = event_div.find('div', {'class': 'body'}).text
    event_website = f'https://www.novaparks.com{href}'
    
    try:
        start_date, start_time = event_div.find(
            'span',
            {'class': 'date-display-start'}
        ).get('content', '').split("T")
        start_time = start_time.split("-")[0]
    except ValueError as e:
        msg = f"Exception getting start date/time for {event_website}: {e}"
        logger.error(msg, exc_info=True)
        return
    
    try:
        end_date, end_time = event_div.find(
            'span',
            {'class': 'date-display-end'}
        ).get('content', '').split("T")
        end_time = end_time.split("-")[0]
    except ValueError as e:
        msg = f"Exception getting end date/time for {event_website}: {e}"
        logger.warning(msg, exc_info=True)
        end_time = start_time
        end_date = start_date
    
    event_venue = event_div.find('p', {'class': 'subhead'}).text
    event_cost = get_event_cost(event_description)
    event_image = event_div.find('img').get('src', '')
    
    event_data = {
        'Event Name': event_name,
        'Event Description': event_description,
        'Event Start Date': start_date,
        'Event Start Time': start_time,
        'Event End Date': end_date,
        'Event End Time': end_time,
        'All Day Event': "False",
        'Timezone': "America/New_York",
        'Event Venue Name': event_venue,
        'Event Organizers': 'NOVA Parks',
        'Event Cost': event_cost,
        'Event Currency Symbol': "$",
        'Event Website': event_website,
        'Event Featured Image': event_image,
        'Event Category': ''
    }
    
    return event_data


def main():
    url = form_url()
    event_divs = scrape(url)
    events = []
    for event_div in event_divs:
        event = get_event_data(event_div)
        if not event:
            continue
        events.append(event)
    return events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    events = main()
    print(len(events))
