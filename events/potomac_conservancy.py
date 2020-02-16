from datetime import datetime
import logging
import os

from bs4 import BeautifulSoup
import requests

from .utils.log import get_logger

logger = get_logger(os.path.basename(__file__))


def soupify_event_page(url):
    try:
        r = requests.get(url)
    except Exception as e:
        msg = f"Exception making GET request to {url}: {e}"
        logger.critical(msg, exc_info=True)
        return
    soup = BeautifulSoup(r.content, 'html.parser')

    return soup


def get_events(soup):
    divs = soup.find_all('div', {'class': 'summary-item'})
    events = []
    for div in divs:
        event = get_event(div)
        if event:
            events.append(event)
    
    return events


def get_start_date(event_time, event_website):
    try:
        datetime_obj = datetime.strptime(event_time, "%b %d, %Y")
        event_start_date = datetime.strftime(datetime_obj, "%Y-%m-%d")
        return event_start_date
    except ValueError as e:
        msg = f"Exception parsing {event_time} from {event_website}: {e}"
        logger.error(msg, exc_info=True)


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
    time_span = soup.find('span', {'class': "event-time-24hr"})
    try:
        time_class = "event-time-24hr-start"
        event_start_time = time_span.find('time', {'class': time_class}).text
    except AttributeError as e:
        msg = f"Unable to scrape start_time from {event_website}: {e}"
        logger.error(msg, exc_info=True)
        return
    try:
        time_class = "event-time-12hr-end"
        event_end_time = time_span.find('time', {'class': time_class}).text
    except AttributeError as e:
        logger.error(f"Unable to scrape event_end_time: {e}", exc_info=True)
        return
    span_class = "eventitem-meta-address-line"
    event_venue = soup.find('span', {'class': span_class}).get_text()
    try:
        li_class = "eventitem-meta-item eventitem-meta-tags event-meta-item"
        cat = soup.find('li', {'class': li_class}).text.replace("Tagged", "")
    except AttributeError:
        cat = ''
    _event_data = {
        'Event Start Time': f'{event_start_time}:00',
        'Event End Time': f'{event_end_time}:00',
        'Event Venue Name': event_venue,
        'Event Category': cat
    }
    event_data.update(_event_data)

    return event_data


def main():
    soup = soupify_event_page('https://potomac.org/events')
    events = get_events(soup)
    
    return events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
