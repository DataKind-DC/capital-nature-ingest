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
    try:
        r = requests.get(event_website)
    except:
        return None, None
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
        event_tags = event['Event Tags']
        event_categories = [x.strip().lower() for x in event_tags.split(",")]
        if not any(x in event_categories for x in categories_lowered):
            filtered_events.append(event)

    return filtered_events


def get_vnps_events(categories=[]):
    '''
    Gets the event data in oour wordpess schema

    Parameters:
        categories (list): a list of categories to filter out. See filter_events docstring for
                           possible values.

    Returns:
        events (list): a list of dicts, with each representing a vnps event
    '''
    try:
        r = requests.get('https://vnps.org/events/')
    except:
        #TODO: log something like this
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
            date_and_time, description_and_location = row.find_all('td')
            all_day, start_time, end_time, start_date, end_date = parse_date_and_time(date_and_time)
            event_website, event_name, event_venue, event_tags = parse_description_and_location(description_and_location)
            event_venue = event_venue if event_venue else ''
            event_tags = event_tags if event_tags else ''
            event = {'Event Start Date': start_date,
                     'Event End Date': end_date,
                     'Event Start Time': start_time,
                     'Event End Time': end_time,
                     'Event Website': event_website,
                     'Event Name': event_name,
                     'Event Venue Name': event_venue,
                     'All Day Event': all_day,
                     'Event Tags': event_tags,
                     'Event Currency Symbol':'$',
                     'Event Time Zone':'Eastern Standard Time',
                     'Event Organizer Name(s) or ID(s)': event_venue}
            events.append(event)
    filtered_events = filter_events(events, categories)

    return filtered_events


def vnps_handler(event, context):
    '''
    AWS lambda function for VNPS events.
    '''
    _ = event['url']
    source_name = event['source_name']
    events = get_vnps_events()
    filename = '{0}-results.csv'.format(source_name)
    fieldnames = list(events[0].keys())
    if not is_local:
        with open('/tmp/{0}'.format(filename), mode = 'w') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            for vnps_event in events:
                writer.writerow(vnps_event)
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file('/tmp/{0}'.format(filename),
                                    bucket,
                                    'capital-nature/{0}'.format(filename)
                                    )
    else:
        with open(filename, mode = 'w') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            for vnps_event in events:
                writer.writerow(vnps_event)

# For local testing (it'll write the csv as vnps-results.csv into your working dir)
#event = {
#'url': 'https://vnps.org',
#'source_name': 'vnps'
#}
#is_local = True
#vnps_handler(event, None)
