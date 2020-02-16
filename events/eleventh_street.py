from datetime import datetime
import logging
import math
import os
import re

from bs4 import BeautifulSoup
import requests

from .utils.log import get_logger

logger = get_logger(os.path.basename(__file__))


def soupify_event_page(url='https://bbardc.org/events/'):
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(f'Exception making GET to {url}: {e}', exc_info=True)
        return
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')

    return soup


def soupify_event_website(event_website):
    try:
        r = requests.get(event_website)
    except Exception as e:
        msg = f'Exception making GET to {event_website}: {e}'
        logger.critical(msg, exc_info=True)
        return
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')

    return soup


def get_event_timing(event_soup):
    all_day_event = False
    start_time = ''
    end_time = ''
    try:
        soup_time = event_soup.find(
            'div',
            class_='tribe-events-start-time').text

        start_time = datetime.strptime(
            soup_time.split(' - ', 1)[0].strip(),
            '%I:%M %p')
        start_time = datetime.strftime(start_time, '%H:%M:%S')
        end_time = datetime.strptime(
            soup_time.split(' - ', 1)[1].strip(), '%I:%M %p')
        end_time = datetime.strftime(end_time, '%H:%M:%S')
    except AttributeError:
        all_day_event = True
    except ValueError as e:
        msg = f'Exception parsing {soup_time}: {e}'
        logger.error(msg, exc_info=True)
    
    return start_time, end_time, all_day_event


def get_event_dates(event_soup):
    start_date = ''
    end_date = ''
    multi_day_event = False
    start_date = event_soup.find('abbr', class_='tribe-events-start-date')
    try:
        if 'title' in start_date.attrs:
            start_date = start_date['title']
    except AttributeError:
        start_date = ''
    try:
        end_date = event_soup.find('abbr', class_='tribe-events-end-date')
        if'title' in end_date.attrs:
            end_date = end_date['title']
    except AttributeError:
        end_date = ''
    if end_date != '':
        multi_day_event = True
    elif end_date == '':
        end_date = start_date
    return start_date, end_date, multi_day_event


def get_event_description(event_site_soup, event_name):
    description = ''
    try:
        soup_paragraphs = event_site_soup.find(
            'div',
            'tribe-events-single-event-description').find_all('p')
        soup_paragraphs = [i.text for i in soup_paragraphs]
        description = ''.join(soup_paragraphs)
    except Exception as e:
        msg = f'Exception finding the event description for {event_name}: {e}'
        logger.error(msg, exc_info=True)
    return description


def get_event_venue(event_site_soup, event_name):
    venue = ''
    try:
        venue = event_site_soup.find('dd', class_='tribe-venue').text
    except AttributeError:
        # try to look in dd tag for the dl tag
        dls = event_site_soup.find_all('dl')
        for dl in dls:
            _venue = dl.find('dd', {'class': 'tribe-venue'})
            if _venue:
                venue += _venue.get_text()
                break
    except Exception as e:
        msg = f'Exception finding the event venue for {event_name}: {e}'  
        logger.error(msg, exc_info=True)
    return venue.strip()


def get_event_category(event_site_soup, event_name):
    category = ''
    try:
        category = event_site_soup.find(
            'dd',
            class_='tribe-events-event-categories').text
    except AttributeError:
        category = ''
    except Exception as e:
        msg = f'Exception finding the event category for {event_name}: {e}'
        logger.error(msg, exc_info=True)
    return category


def get_event_cost(event_site_soup, event_name):
    cost = ''
    try:
        cost = event_site_soup.find(
            'dd',
            class_='tribe-events-event-cost').text.strip()
        if cost.lower() == 'free':
            return '0'
        str_prices = re.findall(r"[-+]?\d*\.\d+|\d+", cost)
        float_prices = [float(f) for f in str_prices]
        cost = str(math.ceil(max(float_prices)))
    except AttributeError:
        cost = ''
    except Exception as e:
        msg = f'Exception finding the event cost for {event_name}: {e}'
        logger.error(msg, exc_info=True)
    return cost


def main():
    soup = soupify_event_page()
    events = soup.find_all('div', class_='tribe_events')
    events_out = []

    for e in events:
        event_name = e.select('h3 > a')[0].text
        event_website = e.select('h3 > a')[0].get("href")
        event_site_soup = soupify_event_website(event_website)
        event_venue = get_event_venue(event_site_soup, event_name)
        if not event_venue:
            continue
        timing = get_event_timing(event_site_soup)
        dates = get_event_dates(event_site_soup)
        event_description = get_event_description(event_site_soup, event_name)
        event_organizers = 'Building Bridges Across the River'
        
        event_category = get_event_category(event_site_soup, event_name)
        event_cost = get_event_cost(event_site_soup, event_name)
        start_time = timing[0]
        all_day = dates[2]
        if not start_time and not all_day:
            continue
        event = {
            'Event Name': event_name,
            'Event Website': event_website,
            'Event Start Date': dates[0],
            'Event Start Time': start_time,
            'Event End Date': dates[1],
            'Event End Time': timing[1],
            'Event Venue Name': event_venue,
            'Timezone': 'America/New_York',
            'Event Cost': event_cost,
            'Event Description': event_description,
            'Event Category': event_category,
            'Event Organizers': event_organizers,
            'Event Currency Symbol': '$',
            'All Day Event': all_day
        }
        events_out.append(event)

    return events_out


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    events = main()
    print(len(events))
