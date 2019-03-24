from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import time
import re
import logging

logger = logging.getLogger(__name__)

def filter_events(events_data):
    '''
    Filter out the Tuesday-Saturday Work Weeks Begins event from the event data.
    
    Parameters:
        events_data (list): a list of dicts, with each dict representing an event.
        
    Returns:
        filtered_data (list): a list of dicts, with each dict representing an event.
    '''
    filtered_data = []
    for event in events_data:
        event_title = event['title']
        if 'Tuesday-Saturday' not in event_title:
            filtered_data.append(event)
    
    return filtered_data

def get_datetime(event_date):
    '''
    Given a 13-digit Linux timestamp, convert that to the schema's date and time format.
    
    Parameters:
        event_date (int or str): a 13-digit linux timestamp. For example, 1550930400562
        
    Returns:
        event_date (str): the date component of the timestamp (e.g. '2019-02-23')
        event_time (str): the time component of the timestamps (e.g. '14:00:00')
    '''
    if not isinstance(event_date, int):
        event_date = int(event_date)
    event_time = time.strftime("%Y-%m-%d,%H:%M:%S", time.gmtime(event_date / 1000.0))
    event_date, event_time = event_time.split(",")
    
    return event_date, event_time

def get_event_description(event_website):
    '''
    Given the event's website, scrape the event's description.
    
    Parameters:
        event_website (str): the event's website
        
    Returns:
        event_description (str): the event's description
    '''
    try:
        r = requests.get(event_website)
    except Exception as e:
        logger.critical(f"Exception making GET request to {event_website}: {e}", 
                        exc_info=True)
        return ''
    soup = BeautifulSoup(r.content, 'html.parser')
    desc_div = soup.find('div',{'class':'sqs-block-content'})
    try:
        event_description = desc_div.get_text()
    except AttributeError:
        return ''
    event_description = event_description.encode('windows-1252', 
                                                 errors = 'ignore').decode("utf8", 
                                                                           errors='ignore')
    event_description = re.sub(r' +',' ', event_description).strip()
    
    return event_description

def get_event_categories(event):
    '''
    Extract the unique tags and categories from the event.
    
    Parameters:
        event (dict): a event as returned by the API
        
    Returns:
        event_categories (str): a comma delimited string of event categories.
    '''
    tags = event['tags']
    categories = event['categories']
    event_categories = ", ".join(set(tags + categories))
    
    return event_categories

def schematize_event(event):
    '''
    Given an event as returned by the API, schematize it.

    Parameters:
        event (dict): an event dict

    Returns:
        schematize_event (dict) = an event in our schema
    '''
    start_date, start_time = get_datetime(event['startDate'])
    end_date, end_time = get_datetime(event['endDate'])
    intervening_days = get_intervening_days(start_date, end_date )
    schematized_events = []
    for intervening_day in intervening_days:
        start_date = intervening_day
        end_date = intervening_day
        event_url = event['fullUrl']
        event_website = f'http://cityblossoms.org{event_url}'
        event_name = event['title']
        try:
            event_venue = event['location']['addressTitle']
        except KeyError:
            #if the addressTitle isn't present, one could use the lat-lon and reverse geocode. But
            #trying that with 2019/2/20/chesapeake-green-2019-a-horticulture-symposium returns an NYC
            #address despite the fact that the pdf linked to on the event's website states the location
            #as somewhere within Maryland. Because of this, we'll not capture events that don't have
            #and addressTitle
            return
        event_venue = event_venue if event_venue else "See event website"
        event_cost = '' #this field isn't returned by the API or on the event's website
        event_description = get_event_description(event_website)
        event_categories = get_event_categories(event)
        event_image = event.get('assetUrl', '')
        schematized_event = {'Event Start Date': start_date,
                             'Event End Date': end_date, 
                             'Event Start Time': start_time,
                             'Event End Time': end_time,
                             'Event Website': event_website,
                             'Event Name': event_name,
                             'Event Venue Name': event_venue,
                             'Event Cost': event_cost,
                             'Event Description': event_description,
                             'Event Currency Symbol':'$',
                             'Timezone':'America/New_York',
                             'Event Organizers':'City Blossoms',
                             'Event Category': event_categories,
                             'All Day Event':False,
                             'Event Featured Image': event_image}
        schematized_events.append(schematized_event)
    
    return schematized_events

def get_intervening_days(start_date, end_date):
    '''
    Given the start and end dates for an event, determine if they're the same day and, if not, return
    an inclusive list of the intervening days.
    
    Parameters:
        start_date (str): a date string like '2019-02-07'
        end_date (str): a date string like '2019-02-07'
        
    Returns:
        intervening_days (list): if the dates aren't the same, a list of the inclusive intervening days
    '''
    start_date = datetime.strptime(start_date,"%Y-%m-%d")
    end_date = datetime.strptime(end_date,"%Y-%m-%d")
    delta = end_date - start_date 
    intervening_days = []
    for i in range(delta.days + 1):
        intervening_day = start_date + timedelta(i)
        intervening_day = intervening_day.strftime("%Y-%m-%d")
        intervening_days.append(intervening_day)
    
    return intervening_days
    
def get_event_data():
    '''
    Returns the results of the city blossoms events API
    '''
    cal = 'http://cityblossoms.org/calendar'
    try:
        r = requests.get(cal)
    except Exception as e:
        logger.critical(f"Exception making GET request to {cal}: {e}", 
                        exc_info=True)
        return
    cookies = r.cookies
    crumb = cookies.get_dict()['crumb']
    month = datetime.now().strftime("%m-%Y")
    url = f'http://cityblossoms.org/api/open/GetItemsByMonth?month={month}&collectionId=55a52dfce4b09a8bb0485083&crumb={crumb}'
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(f"Exception making GET request to {url}: {e}", 
                        exc_info=True)
        return
    events_data = r.json()
    
    return events_data

    
def main():
    events_data = get_event_data()
    if not events_data:
        return []
    filtered_data = filter_events(events_data)
    events = []
    for event in filtered_data:
        schematized_events = schematize_event(event)
        if schematized_events:
            events.extend(schematized_events)
        
    return events

if __name__ == '__main__':
    events = main()
