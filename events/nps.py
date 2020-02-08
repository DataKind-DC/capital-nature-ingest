from datetime import datetime
import logging
import os
import re

from astral import Astral
from bs4 import BeautifulSoup
import requests

try:
    NPS_KEY = os.environ['NPS_KEY']
except KeyError:
    NPS_KEY = input("Enter your NPS API key:")

logger = logging.getLogger(__name__)

PARK_CODES = [
    'afam', 'anac', 'anti', 'apco', 'appa', 'arho', 'asis', 'balt', 'bawa',
    'bepa', 'blri', 'bowa', 'cahi', 'cajo', 'came', 'cato', 'cawo', 'cbgn',
    'cbpo', 'cebe', 'choh', 'clba', 'coga', 'colo', 'cuga', 'cwdw', 'fodu',
    'fofo', 'fomc', 'fomr', 'foth', 'fowa', 'frde', 'frdo', 'frsp', 'gewa',
    'glec', 'gree', 'grfa', 'grsp', 'gwmp', 'hafe', 'haha', 'hamp', 'hatu',
    'jame', 'jthg', 'keaq', 'kowa', 'linc', 'lyba', 'mamc', 'mana', 'mawa',
    'mlkm', 'mono', 'nace', 'nama', 'ovvi', 'oxhi', 'paav', 'pete', 'pisc',
    'pohe', 'prwi', 'rich', 'rocr', 'shen', 'shvb', 'stsp', 'this', 'thje',
    'thst', 'vive', 'wamo', 'waro', 'whho', 'wotr', 'wwii', 'york'
]


def get_park_events(park_code, limit=1000):
    '''
    Get events from the National Parks Service Events API for a given park_code

    Parameters:
        park_code (str): a parkCode from their API
        limit (int): number of results to return per request. Default is 1000

    Returns:
        park_events (list): A list of dicts for each event with 'park' as the 
                            sitetype. The dict structures follow that of the 
                            NPS Events API.
    '''
    park_code_param = f'?parkCode={park_code}'
    limit_param = f'&limit={limit}'
    key_param = f'&api_key={NPS_KEY}'
    params = park_code_param + limit_param + key_param
    url = "https://developer.nps.gov/api/v1/events" + params
    try:
        r = requests.get(url)
    except Exception as e:
        msg = f"{e} making GET request to {url}"
        logger.critical(msg, exc_info=True)
        return []
    r_json = r.json()
    data = r_json['data']
    park_events = []
    for d in data:
        try:
            site_type = d['sitetype']
        except KeyError:
            site_type = d['siteType']
        if site_type == 'park':
            park_events.append(d)

    return park_events


def get_nps_events(park_codes=PARK_CODES):
    '''
    Get all of the events for each park in the park_codes list
    Parameters:
        None
    Returns:
        nps_events (list): a list of events, as returned by get_park_events()
    '''

    nps_events = []
    for park_code in park_codes:
        try:
            park_events = get_park_events(park_code)
            if len(park_events) > 1:
                for park_event in park_events:
                    nps_events.append(park_event)
        except Exception as e:
            msg = f"{e} getting NPS events for this park code: {park_code}"
            logger.error(msg, exc_info=True)
            pass

    return nps_events


def get_exact_loc(event_id):
    '''
    Some parks are large, and the events have a more specific location.
    To get this location, use the event id to find the event page and scrape.

    Parameters:
        event_id (str): unique identifier for this event
    Returns:
        exact_loc (str): the specific location of the event
    '''
    site = f"https://www.nps.gov/planyourvisit/event-details.htm?id={event_id}"
    try:
        r = requests.get(site)
    except Exception as e:
        msg = f"Exception making GET request to {site}: {e}"
        logger.critical(msg, exc_info=True)
        return ''
    content = r.content
    soup = BeautifulSoup(content, "html.parser")
    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    # extract the data from the raw text
    split_text = text.split("\n")
    exact_loc = ''
    for i, line in enumerate(split_text):
        if "Location:" in line:
            try:
                exact_loc += split_text[i + 1]
            except IndexError:
                pass

    return exact_loc


def schematize_event_time(event_time):
    '''
    Converts a time string like '1:30 pm' to 24hr time like '13:30:00'
    '''
    if not event_time:
        return ''
    try:
        datetime_obj = datetime.strptime(event_time, "%I:%M %p")
        schematized_event_time = datetime.strftime(datetime_obj, "%H:%M:%S")
    except ValueError:
        msg = f"Exception schematizing this event time: {event_time}"
        logger.error(msg, exc_info=True)
        schematized_event_time = ''
    
    return schematized_event_time


def parse_cost(cost):
    '''
    Extracts the highest event cost from a string of potentially many costs

    Parameters:
        cost (str): e.g. "The event costs $12.50 per person."

    Returns:
        cost (str): the event cost, e.g. "12"
    '''
    currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
    costs = re.findall(currency_re, cost)
    if costs:
        max_cost = max([float(x.replace("$", '')) for x in costs])
        cost = str(round(int(max_cost + 0.5)))
        return cost
    else:
        return ''


def scrape_event_description(event_website):
    '''
    Scrape the event's description by finding the longest <p> tag text
    
    Parameters:
        event_website (str): the url to an event page
        
    Returns:
        event_description (str): description of the event
    
    '''
    try:
        r = requests.get(event_website)
    except Exception:
        event_description = 'See event website'
        return event_description
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    divs = soup.find_all('div', {'class': 'Truncatable__Content'})
    try:
        event_description = max([d.text for d in divs], key=len).strip()
    except Exception:
        return 'See event website'
    
    return event_description
    

def get_sun_times(event_date):
    '''
    Given an event's data as a string, use the astral module to get the
    times for sunrise and sunset.

    Parameters:
        event_date (str): the date of an vent in "%Y-%m-%d"

    Returns:
        sunrise (str): the time sunrise time
        sunset (str): the sunset time
    '''
    event_date_dt = datetime.strptime(event_date, "%Y-%m-%d")
    city_name = 'Washington DC'
    a = Astral()
    a.solar_depression = 'civil'
    city = a[city_name]
    sun = city.sun(date=event_date_dt, local=True)
    sunrise = sun['sunrise'].time().strftime("%H:%M:%S")
    sunset = sun['sunset'].time().strftime("%H:%M:%S")
    
    return sunrise, sunset


def get_times(nps_event, date, time):
    if not time['timestart']:
        if time['sunsetend']:
            event_start_time, event_end_time = get_sun_times(date)
        else:
            _id = nps_event.get('id')
            msg = f"Can't get times for event_id: {_id}"
            logger.error(msg, exc_info=True)
            return None, None
    else:
        event_start_time = schematize_event_time(time['timestart'])
        event_end_time = schematize_event_time(time['timeend'])

    return event_start_time, event_end_time


def get_desc(nps_event, event_website):
    try:
        desc = nps_event.get('description', '')
        desc_soup = BeautifulSoup(desc, "html.parser")
        event_description = desc_soup.find("p").text
    except AttributeError:
        event_description = ''
    if not event_description:
        event_description = scrape_event_description(event_website)
    
    return event_description


def is_all_day(nps_event):
    if nps_event['isallday'].title() == 'True':
        return True
    else:
        return False


def get_venue(nps_event):
    event_id = nps_event['id']
    exact_loc = get_exact_loc(event_id)
    if exact_loc:
        sub = nps_event['parkfullname'] + ", " + exact_loc
        park_name_w_location = re.sub(' +', ' ', sub)
    else:
        park_name = nps_event['parkfullname']
        park_name_w_location = re.sub(' +', ' ', park_name)
    venue = nps_event['organizationname']
    venue = venue if venue else nps_event['parkfullname']
    venue = re.sub('  +', ' ', venue)
    if "Rock Creek" in venue:
        organizer = "National Park Service, Rock Creek Park"
        return park_name_w_location, organizer
    organizer = "National Park Service"
    return venue, organizer


def get_cost(nps_event):
    if nps_event['isfree']:
        cost = '0'
    else:
        cost = parse_cost(nps_event['feeinfo'])

    return cost


def get_event_site(nps_event):
    event_id = nps_event['id']
    reg_res_url = nps_event['regresurl']
    info_url = nps_event['infourl']
    portal_name = nps_event['portalname']
    if len(reg_res_url) > 0:
        event_site = reg_res_url
    else:
        event_site = (
            'https://www.nps.gov/planyourvisit/'
            f'event-details.htm?id={event_id}'
        )
        try:
            r = requests.get(event_site)
        except Exception as e:
            msg = f"{e} making GET request to {event_site}"
            logger.error(msg, exc_info=True)
        if r.status_code == 404:
            if len(portal_name) > 0:
                event_site = portal_name
            else:
                event_site = info_url
        else:
            event_site = event_site
    
    return event_site


def get_event_image(nps_event):
    try:
        event_image = nps_event['images'][0]['url']
    except IndexError:
        return ''
    if "nps.gov" not in event_image:
        event_image = f"https://www.nps.gov{event_image}"
    
    return event_image


def schematize_nps_event(nps_event):
    '''
    Extract data from the nps event so that it conforms to the wordpress schema

    Parameters:
        nps_event (dict): an NPS event, as returned by the NPS API
    Returns:
        schematized_nps_events (list): a list of dicts, with each as an event
    '''
    date_end = nps_event['datestart']
    date_start = nps_event['dateend']
    if date_start != date_end:
        # it seems there's a discrepancy between the NPS API results
        # and what's displayed on an event's website. This might be an issue
        # to raise with the NPS API maintainers. Until then, ignore
        return []
    
    schematized_nps_events = []
    dates = nps_event['dates']
    for date in dates:
        times = nps_event['times']
        for time in times:
            event_start_time, event_end_time = get_times(nps_event, date, time)
            if not event_start_time and event_end_time:
                continue
            event_name = nps_event['title']
            
            event_all_day = is_all_day(nps_event)
            venue, organizer = get_venue(nps_event)
            venue = venue if venue else "See event website"
            cost = get_cost(nps_event)
            event_tags = ", ".join(nps_event['tags'])
            event_website = get_event_site(nps_event)
            event_description = get_desc(nps_event, event_website)
            event_image = get_event_image(nps_event)
            schematized_nps_event = {
                "Event Name": event_name,
                "Event Description": event_description,
                "Event Start Date": date,
                "Event Start Time": event_start_time,
                "Event End Date": date,
                "Event End Time": event_end_time,
                "All Day Event": event_all_day,
                "Event Venue Name": venue,
                "Event Organizers": organizer,
                "Timezone": 'America/New_York',
                "Event Cost": cost,
                "Event Currency Symbol": "$",
                "Event Category": event_tags,
                "Event Website": event_website,
                "Event Featured Image": event_image
            }
            schematized_nps_events.append(schematized_nps_event)

    return schematized_nps_events


def main():
    '''
    Returns NPS events for VA, DC and MD. Each event is a dict.
    '''
    nps_events = get_nps_events()
    events = []
    for nps_event in nps_events:
        schematized_nps_events = schematize_nps_event(nps_event)
        events.extend(schematized_nps_events)

    return events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
