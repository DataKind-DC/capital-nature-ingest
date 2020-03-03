from datetime import datetime
import logging

from bs4 import BeautifulSoup, Tag
import requests
import re
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from dateutil import parser
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.setrecursionlimit(30000)

logger = logging.getLogger(__name__)


def get_text_with_br(tag, result=''):
    for x in tag.contents:
        if isinstance(x, Tag):  # check if content is a tag
            if x.name == 'br':  # if tag is <br> append it as string
                result += str(x)
            else:  # for any other tag, recurse
                result = get_text_with_br(x, result)
        else:  # if content is NavigableString (string), append
            result += x
    return result


def before(value, a):
    pos_a = value.find(a)
    if pos_a == -1: return ""
    return value[0:pos_a]


def after(value, a):
    # Find and validate first part.
    pos_a = value.rfind(a)
    if pos_a == -1: return ""
    # Returns chars after the found string.
    adjusted_pos_a = pos_a + len(a)
    if adjusted_pos_a >= len(value): return ""
    return value[adjusted_pos_a:]


def soupify_event_page(url):
    try:
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        r = session.get(url, timeout=1, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')

        return soup
    
    except AttributeError:
        soup = 'Soup could not be made'


def get_events(soup):
    articles = soup.find_all('article', {'class': 'cal-brief'})
    events = []
    for article in articles:
        event = get_event(article)
        events.append(event)
    
    return events


def get_event(article):
    div = article.find('div', {'class': 'row'})
    a = div.find('a')
    event_href = a.get('href')
    event_website = event_href
    event_start_time = ''
    event_end_time = ''
    try:
        text_for_time = div.find('p', {'class': 'time'}).get_text()
    except Exception:
        text_for_time = ''
        
    if text_for_time != '':
        try:
            event_times = re.findall(r'\s(\d+\:\d+\s?)', text_for_time)
        except Exception:
            event_times = text_for_time.split('-')
    else:
        event_times = ''
    if event_times != '' and len(event_times) > 1:
        start_time_string = event_times[0]
        start_time = parser.parse(start_time_string)
        event_start_time = datetime.strftime(start_time, '%H:%M:%S')
        
        end_time_string = event_times[-1]
        end_time = parser.parse(end_time_string)
        event_end_time = datetime.strftime(end_time, '%H:%M:%S')
        
    elif event_times != '' and len(event_times) == 1:
        start_time_string = event_times[0]
        start_time = parser.parse(start_time_string)
        event_start_time = datetime.strftime(start_time, '%H:%M:%S')
        end_time = ''
        
    else:
        start_time = ''
        end_time = ''
        
    
    event_data = {'Event Website': event_website,
                 'Event Start Time': event_start_time,
                 'Event End Time': event_end_time}
    event = update_event_data(event_website, event_data)
    return event


def update_event_data(event_website, event_data):
    soup = soupify_event_page(event_website)
    div = soup.find('div', {'class': 'col-sm-9 col-sm-push-3 content'})
    event_description = div.find('p').get_text()
    whitelist = ['p']
    text_with_time = [t for t in div.find_all(text=True) if t.parent.name in whitelist]
    text_for_time = " ".join(text_with_time)
    if event_data['Event Start Time'] == '':
        event_times = re.findall(r'\s(\d+\:\d+\s?)', text_for_time)
    else:
        event_times = ''
    event_start_time = ''
    event_end_time = ''
    if event_times != '' and len(event_times) > 1:
        start_time_string = event_times[0]
        start_time = parser.parse(start_time_string)
        event_start_time = datetime.strftime(start_time, '%H:%M:%S')
        end_time_string = event_times[-1]
        end_time = parser.parse(end_time_string)
        event_end_time = datetime.strftime(end_time, '%H:%M:%S')
    elif event_times != '' and len(event_times) == 1:
        start_time_string = event_times[0]
        start_time = parser.parse(start_time_string)
        event_start_time = datetime.strftime(start_time, '%H:%M:%S')
        end_time = ''
    elif event_times == '':
        event_start_time = event_data['Event Start Time']
        event_end_time = event_data['Event End Time']
    
    event_name = div.find("h2").get_text()
    start_date_string = div.find('h3', {'class': 'date'}).get_text().split('-')[0]
    start_date_string = start_date_string.replace('th', '')
    start_date_string = start_date_string.replace('rd', '')
    start_date_string = start_date_string.replace('st', '')
    if start_date_string != ' ':
        try:
            start_date = datetime.strptime(start_date_string, '%B %d %Y ').strftime('%Y-%m-%d')
        except Exception:
            start_date = datetime.strptime(start_date_string, ' %B %d %Y').strftime('%Y-%m-%d')
    else:
        start_date = ''
    end_date_string = div.find('h3', {'class': 'date'}).get_text().split('-')[1]
    end_date_string = end_date_string.replace('th', '')
    end_date_string = end_date_string.replace('rd', '')
    end_date_string = end_date_string.replace('st', '')
    if end_date_string != ' ':
        try:
            end_date = datetime.strptime(end_date_string, '%B %d %Y ').strftime('%Y-%m-%d')
        except Exception:
            end_date = datetime.strptime(end_date_string, ' %B %d %Y').strftime('%Y-%m-%d')
    else:
        end_date = start_date
    
    event_cost_list = re.findall(r'\$(\d+)', text_for_time)
    if event_cost_list == []:
        event_cost = 'Free' 
    else:
        event_cost = event_cost_list[0]
        
    try:
        event_category = soup.find('li', {'class':"eventitem-meta-item eventitem-meta-tags event-meta-item"}).get_text().replace("Tagged","")
    except AttributeError:
        event_category = ''
        
    event_data.update({'Event Name': event_name,
                       'Event Website': event_website,
                       'Event Name': event_name,
                       'Event Description': event_description,
                       'Event Start Date': start_date,
                       'Event Start Time': event_start_time,
                       'Event End Date': end_date,
                       'Event End Time': event_end_time,
                       'All Day Event': False,
                       'Timezone': 'America/New_York',
                       'Event Venue Name': '',
                       'Event Organizers': 'US National Arboretum',
                       'Event Category': event_category,
                       'Event Cost': event_cost,
                       'Event Currency Symbol': '$'
                      })
    return event_data


def main():
    soup = soupify_event_page('https://www.usna.usda.gov/visit/calendar-of-events')
    events = get_events(soup)
    return events
    
    
if __name__ == '__main__':
    events = main()
    print(len(events))
