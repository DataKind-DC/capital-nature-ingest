from datetime import datetime
import logging

import bs4
import requests

logger = logging.getLogger(__name__)


def fetch_page(url):
    r = requests.get(url)
    content = r.content
    soup = bs4.BeautifulSoup(content, 'html.parser')
    
    return soup


def handle_ans_page(soup):
    events = soup.find_all('a', {'class': 'timely-event'})
    event_output = []
    for e in events:
        all_day = False
        start_date = e.attrs['data-date']
        event_website = e.attrs['href']
        start_time = e.find('div', {'class': 'timely-start-time'}).text.strip()
        if start_time == 'All-day':
            all_day = True
            start_time = ''
        else:
            start_time = schematize_event_time(start_time, event_website)
            if start_time is None:
                continue
        desc = e.find('div', {'class': 'timely-excerpt'}).text.strip()
        desc = desc.replace("\n", '').replace("\t", "")
        venue = e.find('span', {'class': 'timely-venue'}).text.strip()[2:]
        e_name = e.find('div', {'class': 'timely-title'}).find('span').text
        event_data = {
            'Event Name': e_name,
            'Event Organizers': 'Rock Creek Conservancy',
            'Event Venue Name': venue,
            'Event Website': event_website,
            'Event Start Date': start_date,
            'Event Start Time': start_time,
            'Event End Date': start_date,  # TODO: get end date from event site
            'Event End Time': start_time,  # TODO: get end time from event site
            'Event Currency Symbol': '$',
            'Timezone': 'America/New_York',
            'All Day Event': all_day,
            'Event Category': '',
            'Event Description': desc,
            'Event Cost': ''  # TODO: get cost from event website
        }
        event_output.append(event_data)
    
    return event_output


def schematize_event_time(event_time, event_website):
    '''
    Converts a time string like '1:30 pm' to 24hr time like '13:30:00'
    '''
    try:
        datetime_obj = datetime.strptime(event_time, "%I:%M %p")
        schematized_event_time = datetime.strftime(datetime_obj, "%H:%M:%S")
    except ValueError as e:
        schematized_event_time = ''
        if 'Day' in event_time:
            return None
        msg = f'Exception parsing {event_time} for {event_website}: {e}'
        logger.error(msg, exc_info=True)
        return schematized_event_time
    
    return schematized_event_time


def main():
    url = 'https://events.time.ly/8ib56fp'
    soup = fetch_page(url)
    event_output = handle_ans_page(soup)
    
    return event_output


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
