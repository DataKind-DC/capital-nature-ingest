from datetime import datetime
import re
import requests
import csv
from bs4 import BeautifulSoup
import boto3

bucket = 'aimeeb-datasets-public'
is_local = False

def get_arlington_events():
    '''
    Gets animal- and environment-related events for Arlington County (https://today.arlingtonva.us/)

    Parameters:
        None

    Returns:
        event_items (list): a list of dictionaries, each of which represents an event.
    '''
    startDate = datetime.now().strftime("%Y-%m-%d")
    from_param = 0
    uri = f'https://today-service.arlingtonva.us/api/event/elasticevent?&StartDate={startDate}T05:00:00.000Z&EndDate=null&TopicCode=ANIMALS&TopicCode=ENVIRONMENT&ParkingAvailable=false&NearBus=false&NearRail=false&NearBikeShare=false&From={from_param}&Size=5&OrderBy=featured&EndTime=86400000'
    r = requests.get(uri)
    data = r.json()
    count = data['count']
    event_items = []
    while from_param < count:
        if from_param == 0:
            items = data['items']
            for item in items:
                event_items.append(item)
        else:
            uri = f'https://today-service.arlingtonva.us/api/event/elasticevent?&StartDate={startDate}T05:00:00.000Z&EndDate=null&TopicCode=ANIMALS&TopicCode=ENVIRONMENT&ParkingAvailable=false&NearBus=false&NearRail=false&NearBikeShare=false&From={from_param}&Size=5&OrderBy=featured&EndTime=86400000'
            r = requests.get(uri)
            data = r.json()
            items = data['items']
            for item in items:
                event_items.append(item)
        from_param += 5

    return event_items

def html_textraction(html):
    '''
    Extracts text from html using bs4

    Parameters:
        html (str): a string containing html

    Returns:
        text (str): the text extracted from the html
    '''
    if not html:
        text = "See event website."
    else:
        soup = BeautifulSoup(html, 'html.parser')
        p_tags = soup.find_all('p')
        if p_tags:
            text = ''
            for p in p_tags:
                p_text = p.get_text()
                if "Activity #" not in p_text:
                    text += p_text + ' '
            text = text.strip()
        else:
            text = soup.get_text().strip()
    text = re.sub('  +', ' ', text)

    return text


def parse_event_name(event_name):
    '''
    Clarifies the invasive plant removal event names and extracts text from html.

    Parameters:
        event_name (str): the event name as a string

    Returns:
        event_name (str): the parsed event name
    '''
    if any(x in event_name for x in ('RIP','RiP','Invasive Plant Removal')):
        if "Invasive Plant Removal" in event_name:
            parsed_event_name = re.sub('  +','',"".join(i for i in event_name if ord(i)<128)).replace("RiP",'').replace(" - ",'').replace("RIP",'')
            parsed_event_name = re.sub("  +", " ", parsed_event_name).strip()
        else:
            parsed_event_name = re.sub('  +','',"".join(i for i in event_name if ord(i)<128))
            parsed_event_name = parsed_event_name.replace("RiP",'').replace("RIP",'').replace(' - ','')
            parsed_event_name = f'{parsed_event_name} Invasive Plant Removal'
            parsed_event_name = re.sub("  +", " ", parsed_event_name).strip()
        event_name = html_textraction(parsed_event_name)
    else:
        event_name = html_textraction(event_name)

    return event_name

def schematize_events(event_items):
    '''
    Parses the events API output so that it conforms to our schema

    Parameters:
        event_items (list): a list of dictionaries, each of which represents an event.
                            Output by get_arlington_events()

    Returns:
        events (list): a list of dictionaries, each of which represents an event in our schema
    '''
    events = []
    for event_item in event_items:
        event_item = event_item['vwEventWithLocation']
        event_name = parse_event_name(event_item['eventName'])
        if 'Task Force' in event_name or 'Forestry Commission' in event_name:
            continue
        event_description = html_textraction(event_item['eventDsc'])
        start_date = event_item['eventStartDate']
        end_date = event_item['eventEndDate']
        start_time = event_item['eventStartTime']
        end_time = event_item['eventEndTime']
        event_website = event_item['eventUrlText']
        if event_item['freeOfChargeInd']:
            event_cost = 'Free'
        elif event_item['eventCostDsc']:
            event_cost = event_item['eventCostDsc']
        else:
            event_cost =  "See event website."
        event_venue = html_textraction(event_item['locationName'])
        if event_venue == 'Earth Products Yard' or 'Library' in event_venue:
            continue

        event = {'Event Start Date':start_date,
                 'Event End Date': end_date,
                 'Event Start Time':start_time,
                 'Event End Time':end_time,
                 'Event Website':event_website,
                 'Event Name':event_name,
                 'Event Venue Name':event_venue,
                 'Event Cost':event_cost,
                 'Event Description':event_description,
                 'Event Time Zone':'America/New_York',
                 'Event Organizer Name(s) or ID(s)':event_venue,
                 'Event Currency Symbol':'$'}
        events.append(event)

    return events

def arlington_handler(event, context):
    '''
    AWS lambda function for Arlington County events.
    '''
    _ = event['url']
    source_name = event['source_name']
    event_items = get_arlington_events()
    events = schematize_events(event_items)
    filename = '{0}-results.csv'.format(source_name)
    fieldnames = list(events[0].keys())
    if not is_local:
        with open('/tmp/{0}'.format(filename), mode = 'w') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            for arlington_event in events:
                writer.writerow(arlington_event)
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file('/tmp/{0}'.format(filename),
                                    bucket,
                                    'capital-nature/{0}'.format(filename)
                                    )
    else:
        with open(filename, mode = 'w') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            for arlington_event in events:
                writer.writerow(arlington_event)

#For local testing (it'll write the csv as arlington-results.csv into your working dir
#event = {
#'url': 'https://today.arlingtonva.us/',
#'source_name': 'arlington'
#}
#is_local = True
#arlington_handler(event, None)