from events import montgomery, ans, arlington, casey_trees, fairfax, nps, vnps, \
                   sierra_club, dug_network, city_blossoms
from datetime import datetime
import csv
import boto3
import re
import os

def unicoder(value):
    '''
    Given an object, decode to utf-8 after trying to encode as windows-1252

    Paramters:
        value (obj): could be anything, but should be a string

    Returns:
        If value is a string, return a utf-8 decoded string. Otherwise return value.
    '''
    if isinstance(value, str):
        s = value.encode('windows-1252', errors = 'ignore').decode("utf8", errors='ignore')
        s = re.sub(r' +', ' ', s)
        return s
    else:
        return value


def get_events():
    '''
    Combines the events output of all the event scrapers.

    Returns:
        events (list): a list of dicts, with each dict representing a single event.
    '''
    event_sources = [montgomery, ans, arlington, casey_trees, fairfax, nps, vnps,
                     city_blossoms]
    events = []
    for event_source in event_sources:
        try:
            source_events = event_source.main()
        except Exception as e:
            #don't let a single event source's failure break everything
            #TODO: log instead of print
            print("*"*80)
            print(f"Exception raised scraping {event_source.__name__}")
            print(e)
            print("*"*80)
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
    filename = f'cap-nature-events-{now}.csv'
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
    out_path = os.path.join(os.getcwd(), 'tmp', filename)
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
    tmp_path = os.path.join(os.getcwd(), 'tmp')
    tmp_files = [f for f in os.listdir(tmp_path) if os.path.isfile(os.path.join(tmp_path,f))]
    try:
        venue_file = [f for f in tmp_files if 'venues_' in f][0]
    except IndexError:
        #IndexError because there's no past file
        return set()
    venue_file = os.path.join(tmp_path, venue_file)
    venues = []
    with open(venue_file, errors = 'ignore') as f:
        reader = csv.reader(f)
        for i in reader:
            venue = i[0]
            venues.append(venue)
    past_venues = set(venues)
    past_venues.remove('VENUE NAME')
    #os.remove(venue_file)
    
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
    filename = f'cap-nature-venues-{now}.csv'
    out_path = os.path.join(os.getcwd(), 'tmp', filename)
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
    tmp_path = os.path.join(os.getcwd(), 'tmp')
    tmp_files = [f for f in os.listdir(tmp_path) if os.path.isfile(os.path.join(tmp_path,f))]
    try:
        organizer_file = [f for f in tmp_files if 'organizer' in f][0]
    except IndexError:
        #IndexError because there's no past file
        return set() 
    organizer_file = os.path.join(tmp_path, organizer_file)
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
    filename = f'cap-nature-organizers-{now}.csv'
    out_path = os.path.join(os.getcwd(), 'tmp', filename)
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
    events_to_csv(events, is_local, bucket)
    organizers_to_csv(events, is_local, bucket)
    venues_to_csv(events, is_local, bucket)
    
    return events

if __name__ == '__main__':
    events = main()
    print(f'Found {len(events)} events!')
