from datetime import datetime
from itertools import takewhile
import logging
import os
import re

from bs4 import BeautifulSoup
import requests

from .utils.log import get_logger

logger = get_logger(os.path.basename(__file__))


def get_category_id_map(url='https://www.montgomeryparks.org/calendar/'):
    '''
    Gets a mapping of event categories and their page ids

    Parameters:
        url (str): Default value is the calendar page, which contains 
                   filters for each category

    Returns:
        category_id_map (dict): a mapping of categories (e.g. Camp) to their 
                                ids, which are used to construct urls for 
                                webscraping that category's events
    '''
    try:
        r = requests.get(url)
    except Exception as e:
        msg = f"Exception making GET request to {url}: {e}"
        logger.critical(msg, exc_info=True)
        return
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    category_list = soup.find('ul', {'class': 'filters accordion-wrap'})
    category_items = category_list.find_all('li')
    category_id_map = {}
    for category in category_items:
        a_tag = category.find('a')
        category_id_param = a_tag['href']
        category_id = "".join(s for s in category_id_param if s.isdigit())[:-1]
        category_name = a_tag.get_text().strip()
        category_id_map[category_name] = category_id

    return category_id_map


def parse_event_date(event_date, event_website):
    '''
    Extract the start date and start/end times from the event_date string

    Parameters:
        event_date (str): A str of the event's date (e.g. Fri. January 18th, 
                          2019 10:00am 11:00am) 
        event_website (str): the event's website; useful when debugging

    Returns:
        start_date (str): the event's start date
        start_time (str): the event's start time
        end_time (str): the event's end time
    '''
    date_times = re.sub('  +', ' ', event_date)
    split_date = date_times.split()
    start_date = schematize_event_date(split_date, event_website)
    
    filtered_split_date = list(filter(lambda x: x != "-", split_date))
    try:
        start_time = schematize_event_time(
            filtered_split_date[-2],
            event_website
        )
        end_time = schematize_event_time(
            filtered_split_date[-1],
            event_website
        )
    except ValueError:
        # occurs for multi-day events, with some days being all-day.
        #  We can't support this now
        start_time = None
        end_time = None

    return start_date, start_time, end_time


def get_event_description(soup):
    '''
    Gets the event description from the event website's soup
    '''
    p_tags = soup.find_all('p')
    p_texts = [p.get_text() for p in p_tags]
    cookie_str = 'website uses cookies'
    cookie_notice_index = [i for i, s in enumerate(p_texts) if cookie_str in s]
    if cookie_notice_index:
        del p_texts[cookie_notice_index.pop()]
    event_description = max(p_texts, key=len).strip()

    return event_description


def get_event_cost(soup):
    '''
    Gets the event cost (if any) from the event website's soup
    '''
    dls = soup.find_all('dl')
    try:
        fee_text = [x.get_text() for x in dls if 'Fee' in x.get_text()][0]
        try:
            first_digit_index = fee_text.index(
                next(s for s in fee_text if s.isdigit())
            )
            fee_text = fee_text[first_digit_index:]
            event_cost = "".join(takewhile(lambda x: x.isdigit(), fee_text))
        except StopIteration:
            event_cost = ''
    except IndexError:
        event_cost = ''

    return event_cost


def canceled_test(soup, terms=['canceled', 'cancelled']):
    '''
    Returns True if the event has been canceled
    '''
    h1_tags = soup.find_all('h1', {'class': 'section-head'})
    txts = [h.get_text() for h in h1_tags]
    is_canceled = any([i in t.lower() for t in txts for i in terms])

    return is_canceled


def parse_event_website(event_website):
    '''
    Gets the event description and cost by scraping the event website.

    Parameters:
        event_website (str): the url for the event website

    Returns:
        event_description (str): the scraped description of the event
        event_cost (str): the event cost
    '''
    try:
        r = requests.get(event_website)
    except Exception as e:
        msg = f"Exception making GET request to {event_website}: {e}"
        logger.critical(msg, exc_info=True)
        return None, None
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    if canceled_test(soup):
        event_description = None
        event_cost = None
    else:
        event_description = get_event_description(soup)
        event_cost = get_event_cost(soup)

    return event_description, event_cost


def schematize_event_date(split_date, event_website):
    '''
    Converts and event date like 'Sat. March 23rd, 2019' to '2019-03-23'
    '''
    event_date = " ".join(split_date[:4])
    event_date = re.sub(r'(\d)(st|nd|rd|th)', r'\1', event_date)
    try:
        dt_obj = datetime.strptime(event_date, "%a. %B %d, %Y")
        schematized_event_date = datetime.strftime(dt_obj, "%Y-%m-%d")
    except ValueError:
        # See GH #179
        event_date = event_date.replace(" -", "")
        try:
            dt_obj = datetime.strptime(event_date, "%B %d, %Y")
            schematized_event_date = datetime.strftime(dt_obj, "%Y-%m-%d")
        except ValueError as e:
            msg = f"Exception parsing {event_date} from {event_website}: {e}"
            logger.error(msg, exc_info=True)
            schematized_event_date = ''

    return schematized_event_date


def schematize_event_time(event_time, event_website):
    '''
    Converts an event time like '9:00am' to 24hr time like '09:00:00'
    '''
    try:
        dt_obj = datetime.strptime(event_time, "%I:%M%p")
    except ValueError:
        try:
            dt_obj = datetime.strptime(event_time, "%I%p")
        except ValueError as e:
            msg = f"Exception parsing {event_time} from {event_website}: {e}"
            logger.error(msg, exc_info=True)
            return
    except Exception as e:
        msg = f"Exception parsing {event_time} from {event_website}: {e}"
        logger.error(msg, exc_info=True)
        return
    schematized_event_time = datetime.strftime(dt_obj, "%H:%M:%S")

    return schematized_event_time


def parse_event_item(event_item, event_category):
    '''
    Schematizes the event data

    Parameters:
        event_item (bs4 <li> tag): a list element
        event_category (str): the event category (e.g. Hikes)

    Returns:
        event (dict or None): if dict, the schematized event.
    '''
    href = event_item.find('a', href=True)['href']
    if 'https' not in href:
        event_website = f'https://www.montgomeryparks.org{href}'
    else:
        event_website = href
    event_description, event_cost = parse_event_website(event_website)
    if not event_description:
        return
    else:
        try:
            event_date = event_item.find(
                'span',
                {'class': 'time'})\
                .text.strip()\
                .replace("to", '')\
                .replace("Ocber", "October")
        except Exception as e:
            msg = f"Exception parsing date from {event_item}: {e}"
            logger.error(msg, exc_info=True)
            return
        start_date, start_time, end_time = parse_event_date(
            event_date,
            event_website)
        if not all([start_date, start_time, end_time]):
            return
        event_name = event_item.find(
            'span',
            {'class': 'event-name'}).text.strip()
        event_venue = ", ".join([i.get_text() for i in event_item.find_all(
            'span',
            {'class': 'location'})])
        event_venue = event_venue if event_venue else "See event website"
        event = {'Event Start Date': start_date,
                 'Event End Date': start_date,
                 'Event Start Time': start_time,
                 'Event End Time': end_time,
                 'Event Website': event_website,
                 'Event Name': event_name,
                 'Event Venue Name': event_venue,
                 'Event Cost': event_cost,
                 'Event Description': event_description,
                 'Event Category': event_category,
                 'Timezone': 'America/New_York',
                 'Event Organizers': "Montgomery Parks",
                 'Event Currency Symbol': '$',
                 'All Day Event': False}

    return event


def no_events_test(soup):
    '''
    Returns True if there aren't any events on a page
    '''
    h2_tags = soup.find_all('h2')
    h2_texts = [h.get_text() for h in h2_tags]

    return any(i in h2_texts for i in ['No events found'])


def next_page_test(soup):
    '''
    Returns True if there's a next page href
    '''
    a_tags = soup.find_all('a')
    a_texts = [a.get_text() for a in a_tags]

    return any(i in a_texts for i in ['Next Page'])


def get_events(category_id, event_category):
    url = f'https://www.montgomeryparks.org/calendar/?cat={category_id}&v=0'
    try:
        r = requests.get(url)
    except Exception as e:
        msg = f"Exception making GET request to {url}: {e}"
        logger.critical(msg, exc_info=True)
        return [], None
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    if no_events_test(soup):
        events = [], None
        return events
    
    event_item_div = soup.find('div', {'class': 'event-item'})
    event_items = event_item_div.find_all('li')

    events = []
    for event_item in event_items:
        event = parse_event_item(event_item, event_category)
        if event:
            events.append(event)
        else:
            continue

    return events, soup


def get_category_events(event_category, category_id_map):
    '''
    Scrapes all of the events for a given category

    Parameters:
        event_category (str): the event category (e.g. Hikes)

    Returns:
        events (list): a list of dicts, with each dict representing an event. 
                       None if there aren't any events or if the request fails.
    '''
    category_id = category_id_map[event_category]
    events, soup = get_events(category_id, event_category)
    if not soup:
        return events
    
    is_next_page = next_page_test(soup)
    
    page_counter = 2
    while is_next_page:
        url = (
            'https://www.montgomeryparks.org/calendar/page/'
            f'{page_counter}/?cat={category_id}&v=0'
        )
        try:
            r = requests.get(url)
        except Exception:
            break
        content = r.content
        soup = BeautifulSoup(content, 'html.parser')
        if no_events_test(soup):
            break
        else:
            event_item_div = soup.find('div', {'class': 'event-item'})
            event_items = event_item_div.find_all('li')
            for event_item in event_items:
                event = parse_event_item(event_item, event_category)
                if event:
                    events.append(event)
                else:
                    continue
            is_next_page = next_page_test(soup)
            page_counter += 1

    return events


def dedupe_events(events):
    '''
    De-dupes a list of dicts
    '''
    events = [dict(t) for t in set(tuple(item.items()) for item in events)]

    return events


def main():
    event_categories = [
        'Archaeology',
        'Clean Up',
        'Earth Month',
        'Gardens',
        'Hikes',
        'Nature',
        'Trails',
        'Trail Work',
        'Trips',
        'Weed Warrior'
    ]
    category_id_map = get_category_id_map()
    events = []
    for event_category in event_categories:
        category_events = get_category_events(event_category, category_id_map)
        if category_events:
            for category_event in category_events:
                events.append(category_event)
    events = dedupe_events(events)

    return events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
