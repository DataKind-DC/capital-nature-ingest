from events import montgomery, ans, arlington, casey_trees, fairfax, nps, vnps, \
    city_blossoms
from datetime import datetime
import csv
import boto3

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
        source_events = event_source.main()
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
    if not is_local and bucket:
        with open('/tmp/{0}'.format(filename), 
                  mode = 'w', 
                  encoding = 'utf-8',
                  errors = 'ignore') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            for event in events:
                writer.writerow(event)
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file('/tmp/{0}'.format(filename),
                                    bucket,
                                    'capital-nature/{0}'.format(filename)
                                    )
    else:
        with open(filename, 
                  mode = 'w',
                  encoding = 'utf-8',
                  errors = 'ignore') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            for montgomery_event in events:
                writer.writerow(montgomery_event)

def main():
    events = get_events()
    events_to_csv(events)
    
    return(events)

if __name__ == '__main__':
    events = main()
    print(len(events))
