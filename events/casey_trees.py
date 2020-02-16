import ast
from datetime import datetime
import logging
import os
import unicodedata

from bs4 import BeautifulSoup
import re
import requests

from .utils.log import get_logger

logger = get_logger(os.path.basename(__file__))


def fetch_page_soup(url):
    try:
        r = requests.get(url)
    except Exception as e:
        msg = f"Exception making GET request to {url}: {e}"
        logger.critical(msg, exc_info=True)
        return
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    
    return soup


def parse_event_cost(event_cost):
    if event_cost == "Donation":
        event_cost = event_cost.replace("Donation", "0")
        return event_cost
    else:
        currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
        event_cost = re.findall(currency_re, event_cost)
        if len(event_cost) > 0:
            event_cost = event_cost[0].split(".")[0].replace("$", '')
            event_cost = ''.join(s for s in event_cost if s.isdigit())
            return event_cost
        else:
            return ''


def extract_details(soup, websites):
    # extracts the complete details about events
    events_content = soup.find_all('script', {'type': 'application/ld+json'})
    events_complete_data = set()
    for event in events_content:
        for website in websites:
            if(website in event.text.strip()):
                events_complete_data.add(event.text.strip())
    
    return events_complete_data
    

def exract_websites_cats(events_url):
    websites = []
    category_classes = {}
    for row in events_url:
        for column in row.find_all('div'):
            temp = column.text.strip()
            if(temp.isdigit()):
                pass
            else:
                websites.append(column.find('a')['href'])
                cat_dict = ast.literal_eval(column['data-tribejson'])
                cat_dict = cat_dict['categoryClasses'].split(" ")
                cat_classes = ""
                for c in cat_dict:
                    if("tribe-events-category-" in c):
                        if(cat_classes != ""):
                            cat_classes += ","
                        cat_classes += c.replace("tribe-events-category-", "")
                category_classes[column.find('a')['href']] = cat_classes
    
    return websites, category_classes


def apply_ast(events_complete_data):
    try:
        events_complete_data = ast.literal_eval(
            list(events_complete_data)[0])
    except IndexError:
        return []
    except Exception as e:
        msg = f"Exception applying ast: {e}"
        logger.warning(msg, exc_info=True)
        return []
    
    return events_complete_data


def handle_ans_page(soup):
    events_url = soup.find_all('td')
    websites, category_classes = exract_websites_cats(events_url)

    events_complete_data = extract_details(soup, websites)

    # converts the string to dict
    events_complete_data = apply_ast(events_complete_data)

    # extracts the required fields in the output schema
    result_all_event = []
    for con in events_complete_data:
        events_data = {}
        event_venue = con['location']['name']
        if event_venue == 'TBD':
            continue
        event_venue = event_venue if event_venue else "See event website"
        # some html is present in event name default adding this to format it
        events_name_data = BeautifulSoup(con.get('name', ''), 'html.parser')
        events_data['Event Name'] = events_name_data.get_text()
        events_data['Event Website'] = con.get('url', '')
        _site = events_data['Event Website'], ''
        events_data['Event Category'] = category_classes.get(_site)
        start = datetime.strptime(con['startDate'][:-6], "%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(con['endDate'][:-6], "%Y-%m-%dT%H:%M:%S")
        events_data['Event Start Date'] = start.strftime('%Y-%m-%d')
        events_data['Event End Date'] = end.strftime('%Y-%m-%d')
        events_data['Event Start Time'] = start.strftime('%H:%M:%S')
        events_data['Event End Time'] = end.strftime('%H:%M:%S')
        events_data['Timezone'] = "America/New_York"
        events_data['Event Venue Name'] = event_venue
        events_data['Event Featured Image'] = con.get('image', '')
        event_desc = get_event_description(events_data['Event Website'])
        event_desc = event_desc if event_desc else ''
        description = unicodedata.normalize('NFKD', event_desc)
        events_data['Event Description'] = description
        try:
            price = con['offers']['price']
            events_data['Event Cost'] = parse_event_cost(price)
        except KeyError:
            events_data['Event Cost'] = '0'
        events_data['Event Currency Symbol'] = "$"
        events_data['All Day Event'] = False
        events_data['Event Organizers'] = 'Casey Trees'
        # commenting addresss, latitude and longitude fields for
        # now as The WordPress Event plugin doesn't
        # expect these fields, but we might eventually use their Map plugin,
        # which would need those geo fields
        # events_data['address'] = ' '.join(str(x) for x in
        # con['location']['address'].values())
        # commenting the latitude and longtide fields
        # events_data['latitude'] = "no location"
        # events_data['longitude'] = "no location"
        # location = con.get('location', False)
        # if(location):
        #     geo = location.get('geo', False)
        #     if(geo):
        #         events_data['latitude'] = geo.get('latitude',"")
        #         events_data['longitude'] = geo.get('longitude',"")
        #     else:
        #         events_data['latitude'] = "no geo"
        #         events_data['longitude'] = "no geo"
        result_all_event.append(events_data)
    try:
        # checks if next month calender is present and passes the url
        #  to handle_ans_page function
        li = soup.find('li', {'class': 'tribe-events-nav-next'})
        next_url = li.a['href']
        soup = fetch_page_soup(next_url)
        if not soup:
            return result_all_event
        result_all_event.extend(handle_ans_page(soup))
    except TypeError:
        # means we've found the last page
        pass
    except Exception as e:
        msg = f"Exception checking for additional pages: {e}"
        logger.error(msg, exc_info=True)
        return []

    return result_all_event


def get_event_description(url):
    soup = fetch_page_soup(url)
    if not soup:
        return
    events_url = soup.find('meta', {'property': 'og:description'})['content']
    
    return events_url


def main():
    today = datetime.today()
    url = "https://caseytrees.org/events/" + today.strftime("%Y-%m") + "/"
    soup = fetch_page_soup(url)
    if not soup:
        return []
    events = handle_ans_page(soup)
    
    return events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
