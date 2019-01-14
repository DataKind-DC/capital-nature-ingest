import requests
from bs4 import BeautifulSoup
import re
import csv
import boto3

bucket = 'aimeeb-datasets-public'
is_local = False


def get_event_cost_and_description(event_website):
    '''
    Scape the event cost and description from its site.

    Parameters:
        event_website (str): the url for an Arlington County event.

    Returns:
        event_cost (str): the cost of the event, usually 'Free'
        event_description (str): the description of the event
    '''
    r = requests.get(event_website)
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    entry_content = soup.find('div',{'class':'entry-content'})
    try:
        event_description = entry_content.find("br",{"style":"clear:both"}).text
    except AttributeError:
        event_description = ''
    paras = soup.find_all('p')
    for p in paras:
        if "Cost" in p.text:
            event_cost = p.text.split(":")[1].strip()
            return event_cost, event_description
        else:
            continue
    event_cost = ''
    
    return event_cost, event_description


def parse_event_name(event_name):
    '''
    Clarifies the invasive plant removal event names.
    
    Parameters:
        event_name (str): the name of the event scraped from the events page

    Returns:
        parsed_event_name (str): the parsed name of the event
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
        return parsed_event_name
    else:
        parsed_event_name = re.sub("  +", " ", event_name).strip()
        return parsed_event_name


def get_events():
    '''
    Scrapes events from Arlington Country website

    Parameters:
        None
    
    Returns:
        events (list): a list of dicts, with each representing an envent.
    '''
    events = []
    page_counter = 0
    while page_counter < 10:
        if page_counter == 0:
            url = 'https://environment.arlingtonva.us/events/'
        else:
            url = f'https://environment.arlingtonva.us/events/?pno={page_counter}'
        r = requests.get(url)
        content = r.content
        soup = BeautifulSoup(content, "html.parser")
        table = soup.find('table')
        rows = table.findChildren(['tr'])
        for i, row in enumerate(rows):
            if i == 0:
                continue
            else:
                try:
                  start_date, times = [re.sub(" +", " ", x).strip() for x in row.find('td').text.strip().split("\n")]
                except AttributeError:
                  continue
                start_time, end_time = times.split("-")
                event_website = row.find('a')['href']
                event_name = row.find('a').text
                event_name = parse_event_name(event_name)
                try:
                    event_location = row.find('i').text
                except AttributeError:
                    event_location = ''
                event_cost, event_description = get_event_cost_and_description(event_website)
                event = {'Event Start Date': start_date,
                         'Event End Date': start_date,
                         'Event Start Time': start_time,
                         'Event End Time': end_time,
                         'Event Website': event_website,
                         'Event Name': event_name,
                         'Event Venue Name': event_location,
                         'Event Cost': event_cost,
                         'Event Description': event_description}
                events.append(event)
        page_counter += 1

    return events


def arlington_handler(event, context):
    '''
    AWS lambda function for Arlington County events.
    '''
    url = event['url']
    source_name = event['source_name']
    events = get_events()
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


# For local testing (it'll write the csv as nps-results.csv into your working dir)
#event = {
#'url': 'https://environment.arlingtonva.us/events/',
#'source_name': 'arlington'
#}
#is_local = True
#arlington_handler(event, None)