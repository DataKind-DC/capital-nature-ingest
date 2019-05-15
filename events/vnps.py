from bs4 import BeautifulSoup
import requests
from datetime import datetime
from unicodedata import normalize
import logging

logger = logging.getLogger(__name__)


def parse_date_and_time(date_and_time):
    '''
    Get the time-related date from the date-time text.

    Parameters:
        date_and_time(bs4 element tag): a <td> tag

    Returns:
        all_day (bool): True if the event is all-day
        start_time (str or None): if str, the event's start time. If None, the event is an all-day event
        end_time (str or None): if str, the event's end time. If None, the event is an all-day event
        start_date (str): event's start date
        end_date (str): event's end date
    '''
    times = date_and_time.find('br').nextSibling.strip()
    if "-" in times:
        start_time, end_time = [x.strip() for x in times.split("-")]
        all_day = False
    else:
        start_time = None
        end_time = None
        all_day = True
    dates = date_and_time.text.replace(times,'').strip()
    if "-" in dates:
        start_date, end_date = [x.strip() for x in dates.split("-")]
    else:
        start_date = dates.strip()
        end_date = dates.strip()
    if start_time:
        start_time_obj = datetime.strptime(start_time,'%I:%M %p')
        start_time = datetime.strftime(start_time_obj, "%H:%M:%S")
    if end_time:
        end_time_obj = datetime.strptime(end_time,'%I:%M %p')
        end_time = datetime.strftime(end_time_obj, "%H:%M:%S")
    if start_date:
        start_date_obj = datetime.strptime(start_date, "%A, %B %d, %Y")
        start_date = datetime.strftime(start_date_obj, "%Y-%m-%d")
    if end_date:
        end_date_obj = datetime.strptime(end_date, "%A, %B %d, %Y")
        end_date = datetime.strftime(end_date_obj, "%Y-%m-%d")

    return all_day, start_time, end_time, start_date, end_date


def soupify_event_website(event_website):
    '''
    Given an event website, use bs4 to soupify it.
    
    Parameters:
        event_website(str): the url for the website
        
    Returns:
        event_website_soup: a bs4 soup object
    '''
    try:
        r = requests.get(event_website)
    except Exception as e:
        logger.critical(f"Exception making GET request to {event_website}: {e}", 
                        exc_info=True)
        return
    content = r.content
    event_website_soup = BeautifulSoup(content, 'html.parser')
    
    return event_website_soup


def get_event_description(event_website_soup):
    '''
    Given the soup to an event's page, return the longest <p> element as the event's description.
    '''
    paras = event_website_soup.find_all('p')
    description = max([p.text for p in paras], key = len)
    
    return description


def get_event_venue_and_categories(event_website_soup):
    '''
    Gets the event's venue and tags from the event's wesbite

    Parameters:
        event_website(str): the url for the website

    Returns:
        event_venue (str): the event's venue
        event_categories (str): a comma-delimited list of event categories
    '''
    paras = event_website_soup.find_all('p')
    event_venue = ''
    event_categories = ''
    for p in paras:
        p_strong = p.find('strong')
        if p_strong:
            p_strong_text = p_strong.text
            if p_strong_text == 'Location':
                event_venue += p.text.replace('Location','').strip()
            elif p_strong_text == 'Categories':
                a_tags = p.find_all('a')
                if a_tags:
                    event_categories += ", ".join([x.get_text() for x in a_tags])
    
    return event_venue, event_categories


def parse_description_and_location(description_and_location):
    '''
    Gets the event website, name and venue

    Parameters:
        description_and_location (bs4 element tag): a <td> tag

    Returns:
        event_website (str): event's website
        event_name (str): event's name
        event_venue (str): event's venue
        event_description (str): event's description
    '''
    a = description_and_location.find('a',href=True)
    event_website = a['href']
    try:
        event_name = a['title']
    except KeyError:
        event_name = a.get_text().strip()
    event_website_soup = soupify_event_website(event_website)
    if not event_website_soup:
        return None, None, None, None, None
    event_venue, event_categories = get_event_venue_and_categories(event_website_soup)
    if not event_venue:
        event_description = ''
        return event_website, event_name, event_venue, event_categories, event_description
    else:
        event_description = get_event_description(event_website_soup)
    event_description = normalize("NFKD", event_description)

    return event_website, event_name, event_venue, event_categories, event_description


def filter_events(events, categories = []):
    '''
    Filters the events output of get_vnps_events() to only include select categories. Possible options are:
        Blue Ridge Wildflower Society
        Chapter Events
        Extended Field Trip
        Field Trips
        Jefferson
        John Clayton
        Meetings
        New River
        Northern Neck
        Piedmont
        Plant Sales
        Pocahontas
        Potowmack
        Prince William
        Programs
        Shenandoah
        South Hampton Roads
        State Events
        Type of Event
        Upper James River
        Volunteer Opportunities
        Workshop

    Parameters:
        events (list): get_vnps_events() return object, which is a list of dicts, with each
                       dictionary representing an event.
        categories (list): a list of categories to filter out.

    Returns:
        events (list): events that do not contain one of the categories within the categories param
    '''
    categories_lowered = [x.lower() for x in categories]
    filtered_events = []
    for event in events:
        event_categories = event['Event Category']
        event_categories = [x.strip().lower() for x in event_categories.split(",")]
        if not any(x in event_categories for x in categories_lowered):
            filtered_events.append(event)

    return filtered_events


def main(categories=[]):
    '''
    Gets the event data in our wordpess schema

    Parameters:
        categories (list): a list of categories to filter out. See filter_events docstring for
                           possible values.
    Returns:
        events (list): a list of dicts, with each representing a vnps event
    '''
    event_url = 'https://vnps.org/events/'
    try:
        r = requests.get(event_url)
    except Exception as e:
        logger.critical(f"Exception making GET request to {event_url}: {e}", exc_info=True)
        return []
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')
    events = []
    for table in tables:
        table_body = table.find('tbody')
        try:
            rows = table_body.find_all('tr')
        except AttributeError:
            continue
        for row in rows:
            tds = row.find_all('td')
            try:
                date_and_time = tds[0]
                description_and_location = tds[2]
            except IndexError:
                logger.warning(f"No table elements (td tags) found in {row}")
                continue
            all_day, start_time, end_time, start_date, end_date = parse_date_and_time(date_and_time)
            event_website, event_name, event_venue, event_categories, event_description = parse_description_and_location(description_and_location)
            event_venue = event_venue if event_venue else "See event website"
            event_categories = event_categories if event_categories else ''
            event_description = event_description if event_description else "See event website"
            event = {'Event Start Date': start_date,
                     'Event End Date': end_date,
                     'Event Start Time': start_time,
                     'Event End Time': end_time,
                     'Event Website': event_website,
                     'Event Name': event_name,
                     'Event Description': event_description,
                     'Event Venue Name': event_venue,
                     'All Day Event': all_day,
                     'Event Category': event_categories,
                     'Event Cost':'',
                     'Event Currency Symbol':'$',
                     'Timezone':'America/New_York',
                     'Event Organizers': 'Virginia Native Plant Society'}
            events.append(event)
    filtered_events = filter_events(events, categories)

    return filtered_events

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
