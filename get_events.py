from events import montgomery, ans, arlington, casey_trees, fairfax, nps, vnps, \
                   sierra_club, dug_network, city_blossoms, tnc, friends_of_kenilworth_gardens, eleventh_street, \
                   dc_audubon, us_botanic_garden
from datetime import datetime
from datetime import timedelta
import csv
import linecache
import boto3
import re
import string
import sys
import os
import geocoder
import logging

logger = logging.getLogger(__name__)

# defined globally for unicoder function
chars_to_keep = ' '
chars_to_keep += string.punctuation
chars_to_keep += string.ascii_lowercase
chars_to_keep += string.ascii_uppercase
chars_to_keep += string.digits
latinate_chars = 'áéíóúüñ¿¡'
chars_to_keep += latinate_chars
sub_re = re.compile(rf'[^{chars_to_keep}]')

def unicoder(value):
    '''
    Given an object, decode to utf-8 after trying to encode as windows-1252

    Paramters:
        value (obj): could be anything, but should be a string

    Returns:
        If value is a string, return a utf-8 decoded string. Otherwise return value.
    '''
    if not isinstance(value, str):
        return value
    value = re.sub(r' +', ' ', value)
    tokens = value.split()
    v = ''
    for token in tokens:
        if not any(s in token for s in latinate_chars):
            u_token = token.encode('windows-1252', errors = 'ignore').decode("utf8", errors='ignore')
            v += f'{u_token} '
        else:
            u_token = re.sub(sub_re, '', value)
            v += f'{u_token} '
    v = re.sub(r' +', ' ', v)
    v = v.strip()

    return v

def date_filter(events):
    '''Given an event, determine if it occurs within the next 7 months
    Paramters:
        events (list): a list of dicts, with each dict representing an event

    Returns:
        events_filtered (list): a list of dicts, with each dict representing an event
    '''
    events_filtered = []
    for e in events:
        start_date = e.get('Event Start Date','')
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            continue
        except Exception as e:
            logger.error(f"Exception parsing event start date of {start_date}. Here's the event:\n{e}",
                         exc_info = True)
            continue
        too_far_into_the_future = datetime.now() + timedelta(100)
        date_diff = start - too_far_into_the_future
        if date_diff <= timedelta(210):
            events_filtered.append(e)

    return events_filtered

def tag_events_with_state(events):
    '''
    Tries to prepend event descriptions with the abbreviation of the location's state, e.g. DC, VA, MD

    Parameters:
        events (list): a list of dictionaries, with each dict representing an event

    Returns:
        events_with_states (list): the updated list of dictionaries, with each dict representing an event
    '''
    venue_state_map = {}
    events_with_states = []
    for event in events:
        state_abbreviation = re.compile(r'\b[A-Z]{2}\b')
        event_organizer = event['Event Organizers']
        event_venue = event['Event Venue Name']
        va_orgs = ['Arlington Parks', 'Fairfax Parks']
        dc_orgs = ['National Park Service, Rock Creek Park', 'United States Botanic Garden']
        md_orgs = ['Montgomery Parks']
        if event_organizer in va_orgs or 'virginia' in event_venue.lower():
            event_state = '(VA)'
        elif event_organizer in dc_orgs:
            event_state = '(DC)'
        elif event_organizer in md_orgs or 'maryland' in event_venue.lower():
            event_state = '(MD)'
        else:
            event_state = None
        if not event_state:
            if event_venue[0].isdigit():
                m = state_abbreviation.findall(event_venue)
                if 'DC' in m:
                    event_state = '(DC)'
                elif 'VA' in m:
                    event_state = '(VA)'
                elif 'MD' in m:
                    event_state = '(MD)'
                if not event_state:
                    if event_venue in venue_state_map:
                        event_state = venue_state_map[event_venue]
                    else:
                        #split at comma in case there are multiple locations
                        venue = event_venue.split(",")[0]
                        g = geocoder.osm(venue)
                        try:
                            event_state = g.json['raw']['address']['state']
                            event_state = f'({event_state})'
                            venue_state_map[event_venue] = event_state
                        except TypeError:
                            pass
        event_description = event['Event Description']
        if event_state:
            updated_event_description = f'{event_state} {event_description}'
            event['Event Description'] = updated_event_description
        events_with_states.append(event)

    return events_with_states

def get_events():
    '''
    Combines the events output of all the event scrapers.

    Returns:
        events (list): a list of dicts, with each dict representing a single event.
    '''
    event_sources = [montgomery, ans, arlington, casey_trees, fairfax, nps, vnps,
                     sierra_club, dug_network, city_blossoms, tnc, friends_of_kenilworth_gardens, eleventh_street,
                     dc_audubon, us_botanic_garden]
    events = []
    for event_source in event_sources:
        try:
            source_events = event_source.main()
        except Exception as e:
            logger.critical(f'Exception getting events in {event_source.__name__}:  {e}',
                            exc_info = True)
            #TODO: schema test events and write failures to (separate) log
            continue
        unicoded_source_events = [{k: unicoder(v) for k,v in i.items()} for i in source_events]
        events.extend(unicoded_source_events)

    return events

def events_to_csv(events, is_local = True, bucket = None):
    '''
    Void function that writes events to csv, either locally or to an S3 bucket.

    Parameters:
        events (list): a list of dicts, with each dict representing a single event.
        is_local (bool): True if you want to write the csv locally. False if you want to
                         write the csv to S3 (must supply a valid bucket name as well)
        bucket (str or None): the name of the public S3 bucket. None by default.

    Returns:
        None
    '''
    now = datetime.now().strftime("%m-%d-%Y")
    filename = f'cap-nature-events-scraped-{now}.csv'
    fieldnames = {'Do Not Import','Event Name','Event Description','Event Excerpt',
                  'Event Start Date','Event Start Time','Event End Date',
                  'Event End Time','Timezone','All Day Event',
                  'Hide Event From Event Listings','Event Sticky in Month View',
                  'Feature Event','Event Venue Name',
                  'Event Organizers','Event Show Map Link','Event Show Map',
                  'Event Cost','Event Currency Symbol','Event Currency Position',
                  'Event Category','Event Tags','Event Website',
                  'Event Featured Image','Allow Comments',
                  'Event Allow Trackbacks and Pingbacks'}
    out_path = os.path.join(os.getcwd(), 'data', filename)
    if not os.path.exists(os.path.join(os.getcwd(), 'data')):
        os.mkdir(os.path.join(os.getcwd(), 'data'))
    with open(out_path,
              mode = 'w',
              encoding = 'utf-8',
              errors = 'ignore') as f:
        writer = csv.DictWriter(f, fieldnames = fieldnames)
        writer.writeheader()
        for event in events:
            writer.writerow(event)
    if not is_local and bucket:
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(out_path,
                                   bucket,
                                   'capital-nature/{0}'.format(filename)
                                   )

def get_past_venues():
    '''
    Returns a set of event venues from current venue csv in temp/ (if it exists)
    and then deletes that file (if it exists) as it will soon be replaced by a new,
    more updated one.

    Parameters:
        None

    Returns:
        past_venues (set): a set of event venues, or an empty set if there are none
    '''
    data_path = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    data_files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
    try:
        venue_file = [f for f in data_files if 'venues-' in f][0]
    except IndexError:
        #IndexError because there's no past file
        return set()
    venue_file = os.path.join(data_path, venue_file)
    venues = []
    with open(venue_file, errors = 'ignore') as f:
        reader = csv.reader(f)
        for i in reader:
            venue = i[0]
            venues.append(venue)
    past_venues = set(venues)
    past_venues.remove('VENUE NAME')
    os.remove(venue_file)

    return past_venues

def venues_to_csv(events, is_local = True, bucket = None):
    '''
    Void function that writes unique event venues to csv, either locally or to
    an S3 bucket.

    Parameters:
        events (list): a list of dicts, with each dict representing a single event.
        is_local (bool): True if you want to write the csv locally. False if you want to
                         write the csv to S3 (must supply a valid bucket name as well)
        bucket (str or None): the name of the public S3 bucket. None by default.

    Returns:
        None
    '''
    venues = []
    for event in events:
        event_venue = event['Event Venue Name']
        venues.append(event_venue)
    past_venues = get_past_venues()
    unique_venues = set(venues) | past_venues
    now = datetime.now().strftime("%m-%d-%Y")
    filename = f'cap-nature-venues-scraped-{now}.csv'
    out_path = os.path.join(os.getcwd(), 'data', filename)
    if not os.path.exists(os.path.join(os.getcwd(), 'data')):
        os.mkdir(os.path.join(os.getcwd(), 'data'))
    with open(out_path,
              mode = 'w',
              encoding = 'utf-8',
              errors = 'ignore') as f:
        writer = csv.writer(f)
        _venues = ['VENUE NAME']
        _venues.extend(list(unique_venues))
        venues_to_write = _venues
        for venue in venues_to_write:
            writer.writerow([venue])
    if not is_local and bucket:
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(out_path,
                                   bucket,
                                   'capital-nature/{0}'.format(filename)
                                    )

def get_past_organizers():
    '''
    Returns a set of event organizers from current organizer csv in temp/ (if it exists)
    and then deletes that file (if it exists) as it will soon be replaced by a new,
    more updated one.

    Parameters:
        None

    Returns:
        past_organizers (set): a set of event organizers, or an empty set if there are none
    '''
    data_path = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    data_files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path,f))]
    try:
        organizer_file = [f for f in data_files if 'organizers-' in f][0]
    except IndexError:
        #IndexError because there's no past file
        return set()
    organizer_file = os.path.join(data_path, organizer_file)
    organizers = []
    with open(organizer_file) as f:
        reader = csv.reader(f)
        for i in reader:
            organizer = i[0]
            organizers.append(organizer)
    past_organizers = set(organizers)
    past_organizers.remove('Event Organizer Name(s) or ID(s)')
    os.remove(organizer_file)

    return past_organizers

def organizers_to_csv(events, is_local = True, bucket = None):
    '''
    Void function that writes unique event organizers to csv, either locally or to
    an S3 bucket.

    Parameters:
        events (list): a list of dicts, with each dict representing a single event.
        is_local (bool): True if you want to write the csv locally. False if you want to
                         write the csv to S3 (must supply a valid bucket name as well)
        bucket (str or None): the name of the public S3 bucket. None by default.

    Returns:
        None
    '''
    organizers = []
    for event in events:
        event_organizer = event['Event Organizers']
        organizers.append(event_organizer)
    past_organizers = get_past_organizers()
    unique_organizers = set(organizers) | past_organizers
    now = datetime.now().strftime("%m-%d-%Y")
    filename = f'cap-nature-organizers-scraped-{now}.csv'
    out_path = os.path.join(os.getcwd(), 'data', filename)
    if not os.path.exists(os.path.join(os.getcwd(), 'data')):
        os.mkdir(os.path.join(os.getcwd(), 'data'))
    with open(out_path,
              mode = 'w',
              encoding = 'utf-8',
              errors = 'ignore') as f:
        writer = csv.writer(f)
        _organizers = ['Event Organizer Name(s) or ID(s)']
        _organizers.extend(list(unique_organizers))
        organizers_to_write = _organizers
        for org in organizers_to_write:
            writer.writerow([org])
    if not is_local and bucket:
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(out_path,
                                   bucket,
                                   'capital-nature/{0}'.format(filename)
                                    )

def main(is_local = True, bucket = None):
    events = get_events()
    events = tag_events_with_state(events)
    events_to_csv(events, is_local, bucket)
    organizers_to_csv(events, is_local, bucket)
    venues_to_csv(events, is_local, bucket)

    return events

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    logger.info(f'Found {len(events)} events!')
