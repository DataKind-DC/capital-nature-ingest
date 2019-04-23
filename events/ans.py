import bs4
import requests
import unicodedata
import sys
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def soupify_event_page(url = 'https://anshome.org/events-calendar/'):
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(f'Exception making GET to {url}: {e}', exc_info = True)
        return
    content = r.content
    soup = bs4.BeautifulSoup(content, 'html.parser')
    
    return soup

def soupify_event_website(event_website):
    try:
        r = requests.get(event_website)
    except Exception as e:
        logger.critical(f'Exception making GET to {event_website}: {e}', exc_info = True)
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
        logger.warning(f'Exception schematizing this date: {event_time}', exc_info = True)
        schematized_event_time = ''
    
    return schematized_event_time

def main():
    soup = soupify_event_page()
    if not soup:
        sys.exit(1)
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
        try:
            event_venue = e.find('span', {'itemprop': 'name'}).get_text()
        except AttributeError:
            event_venue = "See event website"
        event_venue = event_venue if event_venue else "See event website"
        #TODO: try to get the event cost
        event = {
                 'Event Name': event_name,
                 'Event Website': event_website,
                 'Event Start Date': start_date,
                 'Event Start Time': start_time,
                 'Event End Date': end_date,
                 'Event End Time': end_time,
                 'Event Venue Name': event_venue,
                 'Timezone':'America/New_York',
                 'Event Cost': '',
                 'Event Description': event_description,
                 'Event Category': event_category,
                 'Event Organizers': event_organizers,
                 'Event Currency Symbol':'$',
                 'All Day Event':all_day_event}
        events.append(event)
    
    return events


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()