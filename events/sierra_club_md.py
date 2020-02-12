from datetime import datetime
import logging
import os
import re

from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

try:
    EVENTBRITE_TOKEN = os.environ['EVENTBRITE_TOKEN']
except KeyError:
    EVENTBRITE_TOKEN = input("Enter your Eventbrite Token Key:")


def get_category_name(page):
    if page["category_id"] is None:
        category = 'none'
    else:
        if page["subcategory_id"] is None:
            category = get(page["category_id"], 'categories/').json()["name"]
        else:
            category_name = get(page["category_id"], 'categories/')
            category_name = category_name.json()["name"]
            subcategory_name = get(page["subcategory_id"], 'subcategories/')
            subcategory_name = subcategory_name.json()["name"]
            category = category_name + "::" + subcategory_name
    return category

    
def scrape(event_id, event_cost):
    page = get(event_id, resource='events').json()
    venue = get(page["venue_id"], resource='venues').json()

    start = datetime.strptime(page['start']['local'], '%Y-%m-%dT%H:%M:%S')
    end = datetime.strptime(page['end']['local'], '%Y-%m-%dT%H:%M:%S')
    desc = "(" + venue["address"]["region"] + ") " + page["summary"]
    event_data = {
        'Event Name': page['name']['text'],
        'Event Description': desc,
        'Event Start Date': start.strftime('%Y-%m-%d'),
        'Event Start Time': start.strftime('%H:%M:%S'),
        'Event End Date': end.strftime('%Y-%m-%d'),
        'Event End Time': end.strftime('%H:%M:%S'),
        'All Day Event': "False",
        'Timezone': "America/New_York",
        'Event Venue Name': venue["name"],
        'Event Organizers': 'Sierra Club MD',
        'Event Cost': event_cost,
        'Event Currency Symbol': "$",
        # TODO: parse event data for optional category fields if present
        'Event Category': get_category_name(page),  
        'Event Website': page['url'],
        'Event Featured Image': ""
    }
    return event_data


def get(api_id, resource, params={'token': EVENTBRITE_TOKEN}):
    url = f'https://www.eventbrite.com/o/{api_id}' if resource == 'o' \
        else f'https://www.eventbriteapi.com/v3/{resource}/{api_id}'  
    
    try:
        if resource != 'o':
            r = requests.get(url, params=params) 
        else:
            r = requests.get(url)
    except Exception as e:
        msg = f"Exception making GET request to {url}: {e}"
        logger.critical(msg, exc_info=True)
        return
    if not r.ok:
        code = r.status_code
        msg = f"Non-200 status code of {code} making GET request to: {url}"
        logger.critical(msg, exc_info=True)
      
    return r


def get_live_events(soup):
    live_events = soup.find("article", {"id": "live_events"})
    event_divs = live_events.find_all("div", {"class": "list-card-v2"})
    
    return event_divs
 

def get_cost_events(soup):
    cost = soup.find("span", {"class": "list-card__label"}).text
    cost = cost.lower()
    cost = cost.replace("free", "0")
    cost = re.sub(r'[^\d]+', '', cost)
    if cost == "":
        cost = "0"
    return cost


def main():
    events_array = []
    r = get(14506382808, 'o')
    soup = BeautifulSoup(r.content, 'html.parser')  
    event_a_refs = get_live_events(soup)
    for events in event_a_refs:
        event_cost = get_cost_events(events)
        event_id = events.find("a").get("data-eid")
        events_array.append(scrape(event_id, event_cost))
    
    return events_array


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    events = main()
    print(len(events))