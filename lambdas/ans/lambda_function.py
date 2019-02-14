import bs4
import requests
import json
import csv
import unicodedata
import sys
from datetime import datetime
import boto3

bucket = 'aimeeb-datasets-public'
is_local = False

def soupify_event_page(url):
    try:
        r = requests.get(url)
    except:
        return
    content = r.content
    soup = bs4.BeautifulSoup(content, 'html.parser')
    
    return soup

def soupify_event_website(event_website):
    try:
        r = requests.get(event_website)
    except:
        return
    content = r.content
    soup = bs4.BeautifulSoup(content, 'html.parser')
    
    return soup

def get_event_description(event_website_soup):
    '''
    Scrape the event description from the event website.
    '''
    eventon_full_description = event_website_soup.find('div', {'class':'eventon_desc_in'})
    p_tags = eventon_full_description.find_all('p')
    event_description = "".join(unicodedata.normalize('NFKD',f'{p.get_text()} ') for p in p_tags).strip()
    if not event_description:
        event_desc = event_website_soup.find('div', {'id':'event_desc'})
        if event_desc:
            event_description = unicodedata.normalize('NFKD', event_desc.get_text())
        else:
            event_description = ''
            
    return event_description

def schematize_event_date(event_date):
    '''
    Converts a date like '2019-12-2' to '2019-12-02'
    '''
    event_date = '2019-2-2'
    datetime_obj = datetime.strptime(event_date, "%Y-%m-%d")
    schematized_event_date = datetime.strftime(datetime_obj, "%Y-%m-%d")
    schematized_event_date
    
    return schematized_event_date

def schematize_event_time(event_time):
    '''
    Converts a time string like '1:30 pm' to 24hr time like '13:30:00'
    '''
    try:
        datetime_obj = datetime.strptime(event_time, "%I:%M %p")
        schematized_event_time = datetime.strftime(datetime_obj, "%H:%M:%S")
    except ValueError:
        schematized_event_time = ''
    
    return schematized_event_time

def handle_ans_page(soup):
    events_divs = soup.find_all('div', {'class': 'event'})
    events = []
    for e in events_divs:
        event_name = e.find('span', {'class': 'evcal_event_title'}).text
        event_website =  e.find('a')['href']
        event_website_soup = soupify_event_website(event_website)
        span_time = e.find('p').find('span', {'class': 'evo_time'})
        start_time = schematize_event_time(span_time.find('span', {'class': 'start'}).text)
        end_date = schematize_event_date(e.find('time', {'itemprop': 'endDate'})['datetime'])
        start_date = schematize_event_date(e.find('time', {'itemprop': 'startDate'})['datetime'])
        end_time = schematize_event_time(span_time.find('span', {'class': 'end'}).text.replace('- ', ''))
        event_description = get_event_description(event_website_soup)
        event_category = ''
        event_organizers = 'Audubon Naturalist Society'
        all_day_event = False
        #TODO: try to get the event cost
        event = {
                 'Event Name': event_name,
                 'Event Website': event_website,
                 'Event Start Date': start_date,
                 'Event Start Time': start_time,
                 'Event End Date': end_date,
                 'Event End Time': end_time,
                 'Event Venue Name': e.find('span', {'itemprop': 'name'}).text,
                 'Timezone':'America/New_York',
                 'Event Cost': '',
                 'Event Description': event_description,
                 'Event Category': event_category,
                 'Event Organizers': event_organizers,
                 'Event Currency Symbol':'$',
                 'All Day Event':all_day_event}
        events.append(event)
    
    return events

def handler(event, context):
    url = event['url']
    source_name = event['source_name']
    soup = soupify_event_page(url)
    if not soup:
        sys.exit(1)
    events = handle_ans_page(soup)
    filename = '{0}-results.csv'.format(source_name)
    fieldnames = list(events[0].keys())
    if not is_local:
        with open('/tmp/{0}'.format(filename), mode = 'w') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            for ans_event in events:
                writer.writerow(ans_event)
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file('/tmp/{0}'.format(filename),
                                    bucket,
                                    'capital-nature/{0}'.format(filename)
                                    )
    else:
        with open(filename, mode = 'w') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            for ans_event in events:
                writer.writerow(ans_event)

    return json.dumps(events, indent=2)

# For local testing
# event = {
#   'url': 'https://anshome.org/events-calendar/',
#   'source_name': 'ans'
# }
# is_local = True
# print(handler(event, None))
