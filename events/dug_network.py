import bs4
import html
import json
import re
import requests
import sys
import unicodedata


def soupify_event_page(url='http://dugnetwork.org/events/'):
    try:
        r = requests.get(url)
    except:
        return
    content = r.content
    soup = bs4.BeautifulSoup(content, 'html.parser')

    return soup

def schematize_event_date(event_date):
    '''
    Converts a date like '2019-03-22T00:00:00-04:00' to '2019-03-22'
    '''
    schematize_event_date = event_date[0:10]
    return schematize_event_date

def schematize_event_time(event_time):
    '''
    Converts a time string like '2019-03-22T00:00:00-04:00' to '13:30:00'
    '''
    schematize_event_time = event_time[11:19]
    return schematize_event_time

def get_event_location(location):
    '''
    Get event location
    '''
    event_location = location['name']

    return event_location


def get_event_description(description):
    '''
    Get event description
    '''
    #Decode HTML entitles from the description
    description = html.unescape(description)
    #Remove HTML tags from the description
    TAG_RE = re.compile(r'<[^>]+>')
    description = TAG_RE.sub('', description)
    #Resolving utf-8 issues
    description = unicodedata.normalize("NFKD", description)
    #Removing new line character at the end of the string
    description = description[:-2]
    return description


def main():
    soup = soupify_event_page()
    if not soup:
        sys.exit(1)

    events_divs = soup.findAll('script',{'type':'application/ld+json'})
    events_content = json.loads(events_divs[0].string.strip())

    events = []
    for event in events_content:
        event_name = event['name']
        event_website = event['url']
        start_date = schematize_event_date(event['startDate'])
        end_date = schematize_event_date(event['endDate'])
        start_time = schematize_event_time(event['startDate'])
        end_time = schematize_event_time(event['endDate'])
        if 'location' in event.keys():
            event_venue = get_event_location(event['location'])
        else:
            event_venue = "See event website"
        event_venue = event_venue if event_venue else "See event website"
        event_description = get_event_description(event['description'])
        event_category = event['@type']
        event_organizers = 'DUG Network'
        all_day_event = False
        if start_time != '00:00:00' and all([start_time, end_time]):
            event = {
                     'Event Name': event_name,
                     'Event Website': event_website,
                     'Event Start Date': start_date,
                     'Event Start Time': start_time,
                     'Event End Date': end_date,
                     'Event End Time': end_time,
                     'Event Venue Name': event_venue,
                     'Timezone': 'America/New_York',
                     'Event Cost': '',
                     'Event Description': event_description,
                     'Event Category': event_category,
                     'Event Organizers': event_organizers,
                     'Event Currency Symbol':'$',
                     'All Day Event': all_day_event}
            events.append(event)
    return events


if __name__ == '__main__':
    events = main()
