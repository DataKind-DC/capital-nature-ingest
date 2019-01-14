from bs4 import BeautifulSoup
import requests
import csv
import boto3

bucket = 'aimeeb-datasets-public'
is_local = False

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
    
    return all_day, start_time, end_time, start_date, end_date
                           

def get_event_venue_and_categories(event_website):
    '''
    Gets the event's venue and tags from the event's wesbite
    
    Parameters:
        event_website(str): the url for the website
        
    Returns:
        event_venue (str): the event's venue
        event_tags (str): a comma-delimited list of event tags
    '''
    r = requests.get(event_website)
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    paras = soup.find_all('p')
    event_venue = ''
    event_tags = ''
    for p in paras:
        p_strong = p.find('strong')
        if p_strong:
            p_strong_text = p_strong.text
            if p_strong_text == 'Location':
                event_venue += p.text.replace('Location','').strip()
            elif p_strong_text == 'Categories':
                a_tags = p.find_all('a')
                if a_tags:
                    event_tags += ", ".join([x.text for x in a_tags])
    
    return event_venue, event_tags
    

def parse_description_and_location(description_and_location):
    '''
    Gets the event website, name and venue
    
    Parameters:
        description_and_location (bs4 element tag): a <td> tag
        
    Returns:
        event_website (str): event's website
        event_name (str): event's name
        event_venue (str): event's venue
    '''
    a = description_and_location.find('a',href=True)
    event_website = a['href']
    event_name = a['title']
    try:
        event_venue = description_and_location.find('i').text
    except AttributeError:
        event_venue = None
    scraped_event_venue, event_tags = get_event_venue_and_categories(event_website)
    event_venue = event_venue if event_venue else scraped_event_venue
    
    return event_website, event_name, event_venue, event_tags   


def get_vnps_events():
    '''
    Gets the event data in oour wordpess schema
    
    Parameters:
        None
        
    Returns:
        events (list): a list of dicts, with each representing a vnps event
    '''
    r = requests.get('https://vnps.org/events/')
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
            date_and_time, description_and_location = row.find_all('td')
            all_day, start_time, end_time, start_date, end_date = parse_date_and_time(date_and_time)
            event_website, event_name, event_venue, event_tags = parse_description_and_location(description_and_location)
            event = {'Event Start Date': start_date,
                     'Event End Date': end_date,
                     'Event Start Time': start_time,
                     'Event End Time': end_time,
                     'Event Website': event_website,
                     'Event Name': event_name,
                     'Event Venue Name': event_venue,
                     'All Day Event': all_day,
                     'Event Tags': event_tags}
            events.append(event)
            
    return events
        
# For local testing (it'll write the csv as nps-results.csv into your working dir)
#event = {
#'url': 'https://vnps.org',
#'source_name': 'vnps'
#}
#is_local = True
#vnps_handler(event, None)
