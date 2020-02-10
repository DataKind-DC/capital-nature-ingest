from datetime import datetime
import logging
from unicodedata import normalize

from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)


def parse_date_and_time(date_and_time):
    '''
    Get the time-related date from the date-time text.

    Parameters:
        date_and_time(bs4 element tag): a <td> tag

    Returns:
        all_day (bool): True if the event is all-day
        start_time (str or None): if str, the event's start time. 
            If None, the event is an all-day event
        end_time (str or None): if str, the event's end time. 
            If None, the event is an all-day event
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
    dates = date_and_time.text.replace(times, '').strip()
    if "-" in dates:
        start_date, end_date = [x.strip() for x in dates.split("-")]
    else:
        start_date = dates.strip()
        end_date = dates.strip()
    if start_time:
        start_time_obj = datetime.strptime(start_time, '%I:%M %p')
        start_time = datetime.strftime(start_time_obj, "%H:%M:%S")
    if end_time:
        end_time_obj = datetime.strptime(end_time, '%I:%M %p')
        end_time = datetime.strftime(end_time_obj, "%H:%M:%S")
    if start_date:
        start_date_obj = datetime.strptime(start_date, "%A, %B %d, %Y")
        start_date = datetime.strftime(start_date_obj, "%Y-%m-%d")
    if end_date:
        end_date_obj = datetime.strptime(end_date, "%A, %B %d, %Y")
        end_date = datetime.strftime(end_date_obj, "%Y-%m-%d")

    return all_day, start_time, end_time, start_date, end_date


def soupify_site(site):
    '''
    Given an event website, use bs4 to soupify it.
    
    Parameters:
        site(str): the url for the website
        
    Returns:
        site_soup: a bs4 soup object
    '''
    try:
        r = requests.get(site)
    except Exception as e:
        msg = f"Exception making GET request to {site}: {e}"
        logger.critical(msg, exc_info=True)
        return
    content = r.content
    site_soup = BeautifulSoup(content, 'html.parser')
    
    return site_soup


def get_desc(site_soup):
    '''
    Return the longest <p> element as the event's description.
    '''
    paras = site_soup.find_all('p')
    description = max([p.text for p in paras], key=len)
    
    return description


def get_venue_and_categories(site_soup):
    '''
    Gets the event's venue and tags from the event's wesbite

    Parameters:
        site(str): the url for the website

    Returns:
        venue (str): the event's venue
        cats (str): a comma-delimited list of event categories
    '''
    paras = site_soup.find_all('p')
    venue = ''
    cats = ''
    for p in paras:
        p_strong = p.find('strong')
        if p_strong:
            p_strong_text = p_strong.text
            if p_strong_text == 'Location':
                venue += p.text.replace('Location', '').strip()
            elif p_strong_text == 'Categories':
                a_tags = p.find_all('a')
                if a_tags:
                    cats += ", ".join([x.get_text() for x in a_tags])
    
    return venue, cats


def parse_desc_loc(desc_loc):
    '''
    Gets the event website, name and venue

    Parameters:
        desc_loc (bs4 element tag): a <td> tag

    Returns:
        site (str): event's website
        name (str): event's name
        venue (str): event's venue
        desc (str): event's description
    '''
    a = desc_loc.find('a', href=True)
    site = a['href']
    try:
        name = a['title']
    except KeyError:
        name = a.get_text().strip()
    site_soup = soupify_site(site)
    if not site_soup:
        return None, None, None, None, None
    venue, cats = get_venue_and_categories(site_soup)
    if not venue:
        desc = ''
        return site, name, venue, cats, desc
    else:
        desc = get_desc(site_soup)
    desc = normalize("NFKD", desc)

    return site, name, venue, cats, desc


def filter_events(events, categories=[]):
    '''
    Filters the events output of get_vnps_events() to include some categories.
    Possible options are:
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
        events (list): get_vnps_events() return object as a list of dicts, 
                       with each dictionary representing an event.
        categories (list): a list of categories to filter out.

    Returns:
        events (list): events that do not contain one of the categories 
                       within the categories param
    '''
    categories_lowered = [x.lower() for x in categories]
    filtered_events = []
    for event in events:
        cats = event['Event Category']
        cats = [x.strip().lower() for x in cats.split(",")]
        if not any(x in cats for x in categories_lowered):
            filtered_events.append(event)

    return filtered_events


def main(categories=[]):
    '''
    Gets the event data in our wordpess schema

    Parameters:
        categories (list): a list of categories to filter out.
    Returns:
        events (list): a list of dicts, with each representing a vnps event
    '''
    event_url = 'https://vnps.org/events/'
    try:
        r = requests.get(event_url)
    except Exception as e:
        msg = f"Exception making GET request to {event_url}: {e}"
        logger.critical(msg, exc_info=True)
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
                desc_loc = tds[2]
            except IndexError as e:
                msg = f"No table elements (td tags) found in {row}: {e}"
                logger.error(msg, exc_info=True)
                continue
            res = parse_date_and_time(date_and_time)
            all_day, start_time, end_time, start_date, end_date = res
            site, name, venue, cats, desc = parse_desc_loc(desc_loc)
            venue = venue if venue else "See event website"
            cats = cats if cats else ''
            desc = desc if desc else "See event website"
            event = {'Event Start Date': start_date,
                     'Event End Date': end_date,
                     'Event Start Time': start_time,
                     'Event End Time': end_time,
                     'Event Website': site,
                     'Event Name': name,
                     'Event Description': desc,
                     'Event Venue Name': venue,
                     'All Day Event': all_day,
                     'Event Category': cats,
                     'Event Cost': '',
                     'Event Currency Symbol': '$',
                     'Timezone': 'America/New_York',
                     'Event Organizers': 'Virginia Native Plant Society'}
            events.append(event)
    filtered_events = filter_events(events, categories)

    return filtered_events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
