from datetime import datetime
import logging

from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

def soupify_event_page(url):
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(f"Exception {e} making GET request to", exc_info=True)
        return
    soup = BeautifulSoup(r.content, 'html.parser')

    return soup

def get_events(soup):
    divs = soup.find_all('div', {'class': 'summary-item'})
    events = []
    for div in divs:
        event = get_event(div)
        events.append(event)
    
    return events

def get_start_date(event_time, event_website):
    try:
        datetime_obj = datetime.strptime(event_time, "%b %d, %Y")
        event_start_date = datetime.strftime(datetime_obj, "%Y-%m-%d")
        return event_start_date
    except ValueError:
        logger.error(f"Exception schematizing event time - {event_time} - from {event_website}", exc_info=True)

def get_event(div):
    a = div.find('div', 'summary-thumbnail-outer-container').find('a')
    event_name = a.get('data-title')
    event_href = a.get('href')
    event_website = f'https://potomac.org{event_href}'
    event_image = div.find('img').get('data-image')
    start_date = get_start_date(div.find('time').get_text(), event_website)
    event_description = div.find('p').get_text()

    event_data = {
        'Event Name': event_name,
        'Event Website': event_website,
        'Event Featured Image': event_image,
        'Event Start Date': start_date,
        'Event Description': event_description,
        'Event End Date': start_date,
        'Event Cost': '',
        'Timezone': 'America/New_York',
        'Event Organizers': "Potomac Conservancy",
        'Event Currency Symbol': '$',
        'All Day Event': False
    }
    event = update_event_data(event_website, event_data)
    
    return event

def update_event_data(event_website, event_data):
    soup = soupify_event_page(event_website)
    time_span = soup.find('span', {'class':"event-time-24hr"})
    event_start_time = time_span.find('time', {'class':"event-time-24hr-start"}).get_text()
    event_end_time = time_span.find('time', {'class':"event-time-12hr-end"}).get_text()
    event_venue = soup.find('span', {'class':"eventitem-meta-address-line"}).get_text()
    try:
        event_category = soup.find('li', {'class':"eventitem-meta-item eventitem-meta-tags event-meta-item"}).get_text().replace("Tagged","")
    except AttributeError:
        event_category = ''
    event_data.update({'Event Start Time': f'{event_start_time}:00',
                       'Event End Time': f'{event_end_time}:00',
                       'Event Venue Name': event_venue,
                       'Event Category': event_category})

    return event_data

def main():
    soup = soupify_event_page('https://potomac.org/events')
    events = get_events(soup)
    return events

if __name__ == '__main__':
    events = main()
    print(len(events))