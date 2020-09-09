from datetime import datetime
from datetime import timedelta
import logging
import os
import re

from bs4 import BeautifulSoup
import requests

from .utils.log import get_logger

logger = get_logger(os.path.basename(__file__))


def get_cost(soup):
    currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
    b_tags = soup.find_all('b')
    for b in b_tags:
        if 'Cost' in b.text:
            cost = b.nextSibling.strip()
            cost = re.findall(currency_re, cost)
            if len(cost) > 0:
                cost = cost[0].split(".")[0].replace("$", '')
                cost = ''.join(s for s in cost if s.isdigit())
                return cost
    return ''


def get_event_date_from_event_website(event_website):
    tail = event_website.split('/')[-1]
    if all(s.isdigit() for s in tail):
        event_date = '/'.join([tail[i:i + 2] for i in range(0, len(tail), 2)])
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
        if not event_time_div_text:
            # no event time
            return None, None, None, None
    except Exception as e:
        msg = f'Exception getting event datetimes from {event_website}: {e}'
        logger.error(msg, exc_info=True)
        return None, None, None, None
    if start_date:
        end_date = start_date
    else:
        start_date, end_date = get_event_dates(
            event_time_div_text, 
            event_website)
        if not start_date:
            return None, None, None, None
    start_time, end_time = get_event_times(event_time_div_text)
        
    return start_date, end_date, start_time, end_time


def get_e_desc(soup):
    p_texts = []
    for p in soup.find_all("p"):
        p_text = p.get_text()
        p_texts.append(p_text)
    sorted_descriptions = sorted(p_texts, key=len)
    longest_description = sorted_descriptions[-1].strip()
    if longest_description.startswith('Click to view in Google Maps'):
        e_desc = sorted_descriptions[-3].strip()
    else:
        e_desc = longest_description
    e_desc = e_desc
    if e_desc.startswith('Please wait while we redirect'):
        return
    else:
        if e_desc.startswith("Event Description\n"):
            e_desc = e_desc.replace("Event Description\n", '', 1)
        if e_desc.startswith("("):
            between_parentheses = e_desc[e_desc.find("(") + 1:e_desc.find(")")]
            to_replace = f'({between_parentheses})'
            e_desc = e_desc.replace(to_replace, '').strip()
        if "Golf Course" in e_desc:
            golf_index = e_desc.find("Golf Course")
            e_desc = e_desc[golf_index + 13:]
        
        return e_desc


def get_venue(soup):
    try:
        venue = soup.find('h3').find('span').text.replace(' Location', '')
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
        venue = p_tags[p_tag_index]
        test = [x.strip() for x in venue.get_text().split("\n")]
        venue = next(x for x in test if len(x) > 0)

    return venue


def get_event_dates(event_time_div_text, event_website):
    '''
    Given a str like '3/06/2019 8:00 am to 3/06/2019 8:00 pm'),
    extract the event's start and end dates.
    
    Parameters:
        event_time_div_text (str): the text from the event time div, e.g.
                                   '3/06/2019 8:00 am to 3/06/2019 8:00 pm'
                                   
    Returns:
        start_date (str): e.g. 3/06/2019
        end_date (str): e.g. 3/06/2019
    '''
    date_re = re.compile(r'[\d]{1,2}/[\d]{1,2}/[\d]{4}')
    dates = re.findall(date_re, event_time_div_text)
    try:
        start_date = dates[0]
    except IndexError as e:
        msg = f'Unable to grab start date from {event_website}: {e}'
        logger.error(msg, exc_info=True)
        return None, None
    if len(dates) <= 1:
        end_date = start_date
    else:
        end_date = dates[1]
    
    return start_date, end_date


def get_event_times(event_time_div_text):
    '''
    Given a str like '3/06/2019 8:00 am to 3/06/2019 8:00 pm',
    extract the event's start and end times.
    
    Parameters:
        event_time_div_text (str): the text from the event time div, e.g.
                                   '3/06/2019 8:00 am to 3/06/2019 8:00 pm'
                           
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
        msg = f'Exception makng GET to: {event_website}: {e}'
        logger.critical(msg, exc_info=True)
        return None, None, None, None, None, None, None
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    page_title_lowered = soup.find(
        'div',
        {'class': 'page-title'}).text.strip().lower()
    if 'canceled' in page_title_lowered:
        cost = None
        e_desc = None
        venue = None
        start_date = None
        end_date = None
        start_time = None
        end_time = None
    else:
        cost = get_cost(soup)
        e_desc = get_e_desc(soup)
        venue = get_venue(soup)
        start_date, end_date, start_time, end_time = get_event_date_times(
            soup, 
            event_website
        )

    return cost, e_desc, venue, start_date, end_date, start_time, end_time


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
            schematized_event_date = datetime.strftime(
                datetime_obj,
                "%Y-%m-%d"
            )
        except ValueError:
            # format might be like 012619
            try:
                datetime_obj = datetime.strptime(event_date, "%m%d%y")
                schematized_event_date = datetime.strftime(
                    datetime_obj,
                    "%Y-%m-%d"
                )
            except ValueError as e:
                msg = f'Exception schematzing {event_date}: {e}'
                logger.error(msg, exc_info=True)
                schematized_event_date = ''
    
    return schematized_event_date


def schematize_event_time(event_time):
    '''
    Converts a time string like '1:30 pm' to 24hr time like '13:30:00'
    '''
    try:
        datetime_obj = datetime.strptime(event_time, "%I:%M %p")
        schematized_event_time = datetime.strftime(datetime_obj, "%H:%M:%S")
    except ValueError as e:
        msg = f'Exception schematzing {event_time}: {e}'
        logger.error(msg, exc_info=True)
        schematized_event_time = ''
    
    return schematized_event_time


def get_events(end_date, page):
    url = (
        'https://www.fairfaxcounty.gov/parks/views/'
        'ajax?_wrapper_format=drupal_ajax'
    )
    data = dict(
        view_name='calendar_of_events',
        view_display_id='block_1',
        view_path='/node/840',
        pager_element='0',
        field_locationref_target_id='All',
        field_start_date_value='today',
        field_end_date_value=end_date,
        page=page
    )
    try:
        r = requests.post(url, data=data)
    except Exception as e:
        msg = f'Exception making POST to {url} with {data}: {e}'
        logger.critical(msg, exc_info=True)
        return []
    content = r.json()[4]['data']
    soup = BeautifulSoup(content, 'html.parser')
    title_divs = soup.find_all('div', {'class': 'calendar-title'})
    domain = 'https://www.fairfaxcounty.gov'
    events = []
    for title_div in title_divs:
        event_name = title_div.text.strip()
        try:
            event_website = title_div.find('a', href=True)['href']
        except KeyError:
            # if there's no event website, skip
            continue
        if domain not in event_website:
            event_website = domain + event_website
        res = parse_event_website(event_website)
        cost, e_desc, venue, start_date, end_date, start_time, end_time = res
        venue = venue if venue else "See event website"
        if venue and start_date:
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
                     'Event Venue Name': venue,
                     'Event Cost': cost,
                     'Event Description': e_desc,
                     'Event Currency Symbol': '$',
                     'Timezone': 'America/New_York',
                     'Event Organizers': 'Fairfax Parks',
                     'Event Category': '',
                     'All Day Event': False}
            events.append(event)

    return events


def main():
    end_date = (datetime.today() + timedelta(3 * 30)).strftime("%m/%d/%Y")
    events = []
    for page in range(10):  # unlikely more than 200 events in 3 months
        _events = get_events(end_date, page)
        try:
            # if the last event from the previous page is the same as this
            # page's last event, then this is a dupe page and we're done
            stop = _events[-1] == events[-1]
        except IndexError:
            # occurs on first page when events is an empty list
            if page > 0:
                # occurs if we get to second page without any events on first
                break
            stop = False
        if stop:
            break
        events.extend(_events)
    return events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
