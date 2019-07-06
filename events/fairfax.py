from datetime import datetime
import logging
import re

from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

def get_event_cost(soup):
    currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
    b_tags = soup.find_all('b')
    for b in b_tags:
        if 'Cost' in b.text:
            event_cost = b.nextSibling.strip()
            event_cost = re.findall(currency_re, event_cost)
            if len(event_cost) > 0:
                event_cost = event_cost[0].split(".")[0].replace("$",'')
                event_cost = ''.join(s for s in event_cost if s.isdigit())
                return event_cost
    return ''


def get_event_date_from_event_website(event_website):
    url_tail = event_website.split('/')[-1]
    if all(s.isdigit() for s in url_tail):
        event_date = '/'.join([url_tail[i:i+2] for i in range(0, len(url_tail), 2)])
        event_date_year = f'20{event_date[-2:]}'
        event_date = event_date[:-2] + event_date_year
        event_date = schematize_event_date(event_date)
        return event_date
    else:
        return


def get_event_date_times(soup, event_website):
    start_date = get_event_date_from_event_website(event_website)
    try:
        event_time_div_text = soup.find_all('h5')[-1].text
    except Exception as e:
        logger.error(f'Exception getting event datetimes from {event_website}: {e}', 
                    exc_info = True)
        return None, None, None, None
    if start_date:
        end_date = start_date
    else:
        start_date, end_date = get_event_dates(event_time_div_text)
    start_time, end_time = get_event_times(event_time_div_text)
        
    return start_date, end_date, start_time, end_time





def get_event_description(soup):
    p_texts = []
    for p in soup.find_all("p"):
        p_text = p.get_text()
        p_texts.append(p_text)
    sorted_descriptions = sorted(p_texts, key = len)
    longest_description = sorted_descriptions[-1].strip()
    if longest_description.startswith('Click to view in Google Maps'):
        event_description = sorted_descriptions[-3].strip()
    else:
        event_description = longest_description
    event_description = event_description
    if event_description.startswith('Please wait while we redirect'):
        return
    else:
        if event_description.startswith("Event Description\n"):
            event_description = event_description.replace("Event Description\n",'', 1)
        if event_description.startswith("("):
            between_parentheses = event_description[event_description.find("(")+1:event_description.find(")")]
            to_replace = f'({between_parentheses})'
            event_description = event_description.replace(to_replace,'').strip()
        if "Golf Course" in event_description:
            golf_index = event_description.find("Golf Course")
            event_description = event_description[golf_index+13:]
        return event_description


def get_event_venue(soup):
    try:
        event_venue = soup.find('h3').find('span').get_text().replace(' Location','')
    except AttributeError:
        p_tags = soup.find_all('p')
        p_tag_index = 0
        highest_br_count = 0
        for i, p in enumerate(p_tags):
            try:
                br_count = len(p.findChildren('br'))
            except TypeError:
                continue
            if br_count > highest_br_count:
                p_tag_index = i
            highest_br_count = br_count
        event_venue = p_tags[p_tag_index]
        test = [x.strip() for x in event_venue.get_text().split("\n")]
        event_venue = next(x for x in test if len(x)>0)

    return event_venue

def get_event_dates(event_time_div_text):
    '''
    Given the text from the event time div (e.g. '3/06/2019 8:00 am to 3/06/2019 8:00 pm'),
    extract the event's start and end dates.
    
    Parameters:
        event_time_div_text (str): the text from the event time div
                                   (e.g. '3/06/2019 8:00 am to 3/06/2019 8:00 pm')
                                   
    Returns:
        start_date (str): e.g. 3/06/2019
        end_date (str): e.g. 3/06/2019
    '''
    date_re = re.compile(r'[\d]{1,2}/[\d]{1,2}/[\d]{4}')
    dates = re.findall(date_re, event_time_div_text)
    start_date = dates[0]
    if len(dates) <= 1:
        end_date = start_date
    else:
        end_date = dates[1]
    
    return start_date, end_date

def get_event_times(event_time_div_text):
    '''
    Given the text from the event time div (e.g. '3/06/2019 8:00 am to 3/06/2019 8:00 pm'),
    extract the event's start and end times.
    
    Parameters:
        event_time_div_text (str): the text from the event time div
                                   (e.g. '3/06/2019 8:00 am to 3/06/2019 8:00 pm')
                                   
    Returns:
        start_time (str): e.g. 8:00 am
        end_time (str): e.g. 8:00 pm
    '''
    time_re = re.compile(r'\b((1[0-2]|0?[1-9]):([0-5][0-9]) ([AaPp][Mm]))')
    times = re.findall(time_re, event_time_div_text)
    start_time = times[0][0]
    if len(times) <= 1:
        end_time = start_time
    else:
        end_time = times[1][0]
        
    return start_time, end_time

def parse_event_website(event_website):
    try:
        r = requests.get(event_website)
    except Exception as e:
        logger.critical(f'Exception makng GET to: {event_website}: {e}', 
                        exc_info = True)
        event_cost = None
        event_description = None
        event_venue = None
        start_date = None
        end_date = None
        start_time = None
        end_time = None
        return event_cost, event_description, event_venue, start_date, end_date, start_time, end_time
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    page_title_lowered = soup.find('div', {'class':'page-title'}).text.strip().lower()
    if 'canceled' in page_title_lowered:
        event_cost = None
        event_description = None
        event_venue = None
        start_date = None
        end_date = None
        start_time = None
        end_time = None
    else:
        event_cost = get_event_cost(soup)
        event_description = get_event_description(soup)
        event_venue = get_event_venue(soup)
        start_date, end_date, start_time, end_time = get_event_date_times(soup, event_website)

    return event_cost, event_description, event_venue, start_date, end_date, start_time, end_time

def schematize_event_date(event_date):
    '''
    Converts a date string like '01/27/2019' or '2019-01-27'  to '2019-01-27'
    '''
    try:
        datetime_obj = datetime.strptime(event_date, "%Y-%m-%d")
        return event_date
    except ValueError:
        try:
            datetime_obj = datetime.strptime(event_date, "%m/%d/%Y")
            schematized_event_date = datetime.strftime(datetime_obj, "%Y-%m-%d")
        except ValueError:
            #format might be like 012619
            try:
                datetime_obj = datetime.strptime(event_date, "%m%d%y")
                schematized_event_date = datetime.strftime(datetime_obj, "%Y-%m-%d")
            except ValueError:
                logger.warning(f'Exception schematzing this event date: {event_date}', 
                               exc_info = True)
                schematized_event_date = ''
    
    return schematized_event_date


def schematize_event_time(event_time):
    '''
    Converts a time string like '1:30 pm' to 24hr time like '13:30:00'
    '''
    try:
        datetime_obj = datetime.strptime(event_time, "%I:%M %p")
        schematized_event_time = datetime.strftime(datetime_obj, "%H:%M:%S")
    except ValueError:
        logger.warning(f'Exception schematzing this event time: {event_time}', 
                        exc_info = True)
        schematized_event_time = ''
    
    return schematized_event_time


def main():
    cal = 'https://www.fairfaxcounty.gov/parks/park-events-calendar'
    try:
        r = requests.get(cal)
    except Exception as e:
        logger.critical(f'Exception making GET to {cal}: {e}', exc_info = True)
        return []
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    title_divs = soup.find_all('div', {'class':'calendar-title'})
    domain = 'https://www.fairfaxcounty.gov'
    events = []
    for title_div in title_divs:
        event_name = title_div.text.strip()
        try:
            event_website = title_div.find('a', href=True)['href']
        except KeyError:
            #if there's no event website, skip since we won't get needed info without it
            continue
        if not domain in event_website:
            event_website = domain + event_website
        event_cost, event_description, event_venue, start_date, end_date, start_time, end_time = parse_event_website(event_website)
        event_venue = event_venue if event_venue else "See event website"
        if event_venue and start_date:
            start_date = schematize_event_date(start_date)
            end_date = schematize_event_date(end_date)
            start_time = schematize_event_time(start_time)
            end_time = schematize_event_time(end_time)
            event = {'Event Start Date': start_date,
                     'Event End Date': end_date, 
                     'Event Start Time': start_time,
                     'Event End Time': end_time,
                     'Event Website': event_website,
                     'Event Name': event_name,
                     'Event Venue Name': event_venue,
                     'Event Cost': event_cost,
                     'Event Description': event_description,
                     'Event Currency Symbol':'$',
                     'Timezone':'America/New_York',
                     'Event Organizers':'Fairfax Parks',
                     'Event Category':'',
                     'All Day Event':False} #doesn't seem like any events are all day
            events.append(event)

    return events

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
