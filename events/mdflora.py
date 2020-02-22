from datetime import datetime
import logging
import math
import os
import re
import json

from bs4 import BeautifulSoup
import requests

from .utils.log import get_logger

logger = get_logger(os.path.basename(__file__))


def soupify_event_page(url='https://mdflora.org/calendar'):
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
            'li',
            class_='eventInfoStartTime')
        soup_time = soup_time.find('div', class_='eventInfoBoxValue').text

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
    # '%Y-%m-%d'
    try:
        start_date = event_soup.find('li', class_='eventInfoStartDate')
        start_date = start_date.find('div', class_='eventInfoBoxValue').text

    except AttributeError:
        start_date = ''
    try:
        end_date = event_soup.find('li', class_='eventInfoStartDate')
        end_date = end_date.find('div', class_='eventInfoBoxValue').text
    except AttributeError:
        end_date = ''
    return start_date, end_date


def get_event_description(event_site_soup, event_name):
    description = ''
    try:
        soup_paragraphs = event_site_soup.find(
            'div',
            'gadgetEventEditableArea').find_all('p')
        soup_paragraphs = [i.text for i in soup_paragraphs]
        description = ''.join(soup_paragraphs)
    except Exception as e:
        msg = f'Exception finding the event description for {event_name}: {e}'
        logger.error(msg, exc_info=True)
    return description


def get_event_venue(event_site_soup, event_name):
    venue = ''
    try:
        venue_soup = event_site_soup.find('li', class_='eventInfoLocation')
        venue = venue_soup.find("span").text
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
    events = soup.find_all('td', class_='EventListCalendarItemDefault')
    events_out = []

    for e in events:
        try:
            event_name = e.select('div > a')[0].text
            event_website = e.select('div > a')[0].get("href")
            event_site_soup = soupify_event_website(event_website)
            event_venue = get_event_venue(event_site_soup, event_name)
            timing = get_event_timing(event_site_soup)
            dates = get_event_dates(event_site_soup)
            date_start = datetime.strptime(dates[0], '%m/%d/%Y')
            date_start = date_start.strftime('%Y-%m-%d')
            date_end = datetime.strptime(dates[1], '%m/%d/%Y')
            date_end = date_end.strftime("%m/%d/%Y")
            event_description = get_event_description(
                event_site_soup, event_name)
            event_organizers = 'Maryland Native Plant Society'
            event = {
                'Event Name': event_name,
                'Event Website': event_website,
                'Event Start Date': date_start,
                'Event Start Time': timing[0],
                'Event End Date': date_end,
                'Event End Time': timing[1],
                'Event Venue Name': event_venue,
                'Timezone': 'America/New_York',
                'Event Cost': "",
                'Event Description': event_description,
                'Event Category': "",
                'Event Organizers': event_organizers,
                'Event Currency Symbol': '$',
                'All Day Event': "FALSE"
            }
            events_out.append(event)

        except AttributeError:
            continue
        except Exception:
            continue
      
    return events_out


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    events = main()
    print(json.dumps(events, indent=4, sort_keys=True))