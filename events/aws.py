from datetime import datetime
import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def get_event_times(event_soup):
    strongs = event_soup.find_all('strong')
    strong_texts = [s.get_text().replace('<strong>', '') for s in strongs]
    # do this to avoid IndexError below when slicing text
    strong_texts = [f'{s} ' for s in strong_texts]
    date_data = [t.strip() for t in strong_texts if t.strip()[0].isdigit()]
    try:
        start, end = date_data
        start_dt = datetime.strptime(start, "%m/%d/%y %I:%M %p")
        start_date = start_dt.strftime("%Y-%m-%d")
        start_time = start_dt.strftime("%H:%M:%S")
        end_dt = datetime.strptime(end, "%m/%d/%y %I:%M %p")
        end_date = end_dt.strftime("%Y-%m-%d")
        end_time = end_dt.strftime("%H:%M:%S")
        all_day = False
    except ValueError:
        # occurs when there's one date to extract, meaning there's no end time
        start = date_data[0]
        start_dt = datetime.strptime(start, "%m/%d/%y")
        start_date = start_dt.strftime("%Y-%m-%d")
        start_time = ''
        end_time = ''
        end_date = start_date
        all_day = True
    
    return start_date, start_time, end_date, end_time, all_day


def get_event_categories(event_soup):
    i_tag = event_soup.find('i', class_='fa fa-folder fa-fw')
    sib_gen = i_tag.nextSiblingGenerator()
    categories = []
    for s in sib_gen:
        try:
            event_category = s.get_text().strip()
            categories.append(event_category)
        except AttributeError:
            continue
        except Exception as e:
            msg = f"Exception get event categories: {e}"
            logger.warning(msg, exc_info=True)
    
    event_categories = ",".join(categories)
    
    return event_categories


def get_event_description(event_li):
    rendered_content = event_li.renderContents()
    try:
        start_desc_i = event_li.renderContents().index(b'description"&gt;')
    except ValueError:
        # subsection not found so try another
        start_desc_i = event_li.renderContents().index(b'description&quot;&gt')
    start_desc_i += len('description"&gt;')
    desc = rendered_content[start_desc_i:].strip().decode()
    end_desc_ix = desc.index('\t')
    event_description = desc[:end_desc_ix]
    event_description = event_description.replace(";&gt;", "").strip()

    return event_description
    

def get_event_url(event_li):
    href = event_li.find(
        'a',
        class_='rsttip rse_event_link',
        href=True).get('href')
    if href.startswith('http'):
        event_url = href
    else:
        event_url = f'https://www.anacostiaws.org{href}'
    
    return event_url


def soupify_event_url(event_url):
    r = requests.get(event_url)
    content = r.content
    event_soup = BeautifulSoup(content, 'html.parser')
    
    return event_soup


def get_event_venue(event_soup):
    i_tag = event_soup.find('i', class_='fa fa-map-marker fa-fw')
    sib_gen = i_tag.nextSiblingGenerator()
    venues = []
    for s in sib_gen:
        try:
            venue = s.get_text().strip()
            venues.append(venue)
        except AttributeError:
            continue
        except Exception as e:
            msg = f"Exception get event venue: {e}"
            logger.warning(msg, exc_info=True)
    event_venue = ", ".join(venues)
    
    return event_venue


def main():
    calendar_url = 'https://www.anacostiaws.org/events-calendar.html'
    r = requests.get(calendar_url)
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    event_names = soup.find_all('span', class_='event-name')
    event_names = [e.text.replace('WAITLIST - ', '') for e in event_names]
    event_li_list = soup.find_all('li', class_='event')
    events = []
    for event_name, event_li in zip(event_names, event_li_list):
        event_description = get_event_description(event_li)
        event_url = get_event_url(event_li)
        event_soup = soupify_event_url(event_url)
        _times = get_event_times(event_soup)
        start_date, start_time, end_date, end_time, all_day = _times
        event_categories = get_event_categories(event_soup)
        
        event_venue = get_event_venue(event_soup)
        
        event = {
            'Event Start Date': start_date,
            'Event End Date': end_date,
            'Event Start Time': start_time,
            'Event End Time': end_time,
            'Event Website': event_url,
            'Event Name': event_name,
            'Event Venue Name': event_venue,
            'Event Cost': 'Free',
            'Event Description': event_description,
            'Event Currency Symbol': '$',
            'Timezone': 'America/New_York',
            'Event Organizers': 'Anacostia Watershed Society',
            'Event Category': event_categories,
            'All Day Event': all_day
        }
        events.append(event)
        
    return events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
