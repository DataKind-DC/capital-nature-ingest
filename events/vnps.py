from bs4 import BeautifulSoup
import requests
from datetime import datetime


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


def get_event_venue_and_categories(event_website):
    '''
    Gets the event's venue and tags from the event's wesbite

    Parameters:
        event_website(str): the url for the website

    Returns:
        event_venue (str): the event's venue
        event_categories (str): a comma-delimited list of event categories
    '''
    try:
        r = requests.get(event_website)
    except:
        return None, None
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    paras = soup.find_all('p')
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
    '''
    a = description_and_location.find('a',href=True)
    event_website = a['href']
    event_name = a['title']
    try:
        event_venue = description_and_location.find('i').text
    except AttributeError:
        event_venue = None
    scraped_event_venue, event_categories = get_event_venue_and_categories(event_website)
    event_venue = event_venue if event_venue else scraped_event_venue

    return event_website, event_name, event_venue, event_categories


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
            event_website, event_name, event_venue, event_categories = parse_description_and_location(description_and_location)
            if not event_venue:
                #TODO: attempt to get the event venue for these events
                #e.g. https://vnps.org/events/texas-hill-country-field-trip/
                #e.g. https://vnps.org/events/texas-hill-country-field-trip/
                #they're tough since the location isn't listed on
                #https://vnps.org/events/ nor on their event pages
                continue
            else:
                event_categories = event_categories if event_categories else ''
                event = {'Event Start Date': start_date,
                        'Event End Date': end_date,
                        'Event Start Time': start_time,
                        'Event End Time': end_time,
                        'Event Website': event_website,
                        'Event Name': event_name,
                        'Event Description':'',
                        'Event Venue Name': event_venue,
                        'All Day Event': all_day,
                        'Event Category':event_categories,
                        'Event Cost':'',
                        'Event Currency Symbol':'$',
                        'Timezone':'America/New_York',
                        'Event Organizers': 'Virginia Native Plant Society'}
                events.append(event)
    filtered_events = filter_events(events, categories)

    return filtered_events

if __name__ == '__main__':
    events = main()
