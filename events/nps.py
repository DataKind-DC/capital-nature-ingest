import requests
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime
import json
import logging
from astral import Astral
# For a local run, be sure to create an env variable with the NPS API key. 
# For example:
# $ export NPS_KEY=<NPS API Key>
try:
    NPS_KEY = os.environ['NPS_KEY']
except KeyError:
    #if it's not an env var, then we might be testing
    NPS_KEY = input("Enter your NPS API key:")

logger = logging.getLogger(__name__)

def get_park_events(park_code, limit=1000):
    '''
    Get events data from the National Parks Service Events API for a given park_code

    Parameters:
        park_code (str): a park_code as returned by the NPS parkCode API through get_park_codes_by_state()
        limit (int): number of results to return per request. Default is 1000

    Returns:
        park_events (list): A list of dicts representing each event with 'park' as the siteType.
                            The dict structures follow that of the NPS Events API.
    '''
    park_code_param = f'?parkCode={park_code}'
    limit_param = f'&limit={limit}'
    key_param = f'&api_key={NPS_KEY}'
    url = "https://developer.nps.gov/api/v1/events"+park_code_param+limit_param+key_param
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(f"Exception making GET request to {url}: {e}", exc_info=True)
        return []
    r_json = r.json()
    data = r_json['data']
    park_events = []
    for d in data:
        if d['siteType'] == 'park':
            park_events.append(d)
    

    return park_events

def get_nps_events(park_codes = ['afam','anac','anti','apco','appa','arho','asis','balt','bawa','bepa','blri',
                                 'bowa','cahi','cajo','came','cato','cawo','cbgn','cbpo','cebe','choh','clba',
                                 'coga','colo','cuga','cwdw','fodu','fofo','fomc','fomr','foth','fowa','frde',
                                 'frdo','frsp','gewa','glec','gree','grfa','grsp','gwmp','hafe','haha','hamp',
                                 'hatu','jame','jthg','keaq','kowa','linc','lyba','mamc','mana','mawa','mlkm',
                                 'mono','nace','nama','ovvi','oxhi','paav','pete','pisc','pohe','prwi','rich',
                                 'rocr','shen','shvb','stsp','this','thje','thst','vive','wamo','waro','whho',
                                 'wotr','wwii','york']):
    '''
    Get all of the events for each park in the park_codes list
    Parameters:
        None
    Returns:
        nps_events (list): a list of events, as returned by get_park_events()
    '''

    nps_events = []
    for park_code in park_codes:
        try:
            park_events = get_park_events(park_code)
            if len(park_events) > 1:
                for park_event in park_events:
                    nps_events.append(park_event)
        except Exception as e:
            logger.error(f"Exception getting NPS events for this park code: {park_code}: {e}", 
                         exc_info=True)
            pass

    return nps_events

def get_specific_event_location(event_id):
    '''
    Some parks are large, and the events have a more specific location than just the park name.
    To get this location, use the event id to find the event page and then scrape that specific
    location from the page.

    Parameters:
        event_id (str): unique identifier for this event
    Returns:
        specific_event_location (str): the specific location of the event
    '''
    website = f"https://www.nps.gov/planyourvisit/event-details.htm?id={event_id}"
    try:
        r = requests.get(website)
    except Exception as e:
        logger.critical(f"Exception making GET request to {website}: {e}", exc_info=True)
        return ''
    content = r.content
    soup = BeautifulSoup(content, "html.parser")
    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    #extract the data from the raw text
    split_text = text.split("\n")
    specific_event_location = ''
    for i,line in enumerate(split_text):
        if "Location:" in line:
            try:
                specific_event_location += split_text[i+1]
            except IndexError:
                pass

    return specific_event_location

def schematize_event_time(event_time):
    '''
    Converts a time string like '1:30 pm' to 24hr time like '13:30:00'
    '''
    if not event_time:
        return ''
    try:
        datetime_obj = datetime.strptime(event_time, "%I:%M %p")
        schematized_event_time = datetime.strftime(datetime_obj, "%H:%M:%S")
    except ValueError:
        logger.warning(f"Exception schematizing this event time: {event_time}", exc_info=True)
        schematized_event_time = ''
    
    return schematized_event_time

def parse_event_cost(event_cost):
    '''
    Extracts the highest event cost from a string of potentially many costs

    Parameters:
        event_cost (str): e.g. "The event costs $12.50 per person."

    Returns:
        event_cost (str): the event cost, e.g. "12"
    '''
    currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
    event_costs = re.findall(currency_re, event_cost)
    if event_costs:
        max_event_cost = max([float(x.replace("$",'')) for x in event_costs])
        event_cost = str(round(int(max_event_cost + 0.5)))
        return event_cost
    else:
        return ''

def scrape_event_description(event_website):
    '''
    Givent the event's website, scrape the event's description by finding the lost <p> tag text
    
    Parameters:
        event_website (str): the url to an event page
        
    Returns:
        event_description (str): description of the event
    
    '''
    try:
        r = requests.get(event_website)
    except:
        event_description = 'See event website'
        return event_description
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    divs = soup.find_all('div', {'class':'Truncatable__Content'})
    try:
        event_description = max([d.text for d in divs], key = len).strip()
    except:
        return 'See event website'
    
    return event_description
    
def schematize_nps_event(nps_event):
    '''
    Extract data from the nps event so that it conforms to the wordpress schema.

    Parameters:
        nps_event (dict): an NPS event, as returned by the NPS API
    Returns:
        schematized_nps_events (list): a list of dicts, with each dict representing an event
    '''
    date_end = nps_event['dateStart']
    date_start = nps_event['dateEnd']
    if date_start == date_end:
        schematized_nps_events = []
        dates = nps_event['dates']
        for date in dates:
            times = nps_event['times']
            for time in times:
                if not time['timeStart']:
                    if time['sunsetEnd']:
                        event_start_time, event_end_time = get_sun_times(date)
                    else:
                        print("!")
                        continue
                else:
                    event_start_time = schematize_event_time(time['timeStart'])
                    event_end_time = schematize_event_time(time['timeEnd'])
                event_name = nps_event['title']
                try:
                    event_description = BeautifulSoup(nps_event['description'], "html.parser").find("p").text
                except AttributeError:
                    event_description = ''
                event_all_day = nps_event['isAllDay']
                event_id = nps_event['id']
                specific_event_location = get_specific_event_location(event_id)
                if specific_event_location:
                    park_name_w_location = re.sub(' +', ' ', nps_event['parkFullName'] + ", " + specific_event_location)
                else:
                    park_name_w_location = re.sub(' +', ' ', nps_event['parkFullName'])
                event_venue = nps_event['organizationName']
                event_venue = event_venue if event_venue else nps_event['parkFullName']
                event_venue = re.sub('  +', ' ', event_venue)
                event_cost = '0' if nps_event['isFree'] else parse_event_cost(nps_event['feeInfo'])
                _ = nps_event['category']
                event_tags = ", ".join(nps_event['tags'])
                regResURL = nps_event['regResURL']
                infoURL = nps_event['infoURL']
                portalName = nps_event['portalName']
                if len(regResURL) > 0:
                    event_website = regResURL
                else:
                    event_site = f"https://www.nps.gov/planyourvisit/event-details.htm?id={event_id}"
                    try:
                        r = requests.get(event_site)
                    except Exception as e:
                        logger.error(f"Exception making GET request to {event_site}: {e}", 
                                        exc_info=True)
                    if r.status_code == 404:
                        if len(portalName) > 0:
                            event_website = portalName
                        else:
                            event_website = infoURL
                    else:
                        event_website = event_site
                try:
                    event_image = nps_event['images'][0]['url']
                except IndexError:
                    event_image = ''
                if event_image:
                    if "nps.gov" not in event_image:
                        event_image = f"https://www.nps.gov{event_image}"
                if "Rock Creek" in event_venue:
                    event_organizer = "National Park Service, Rock Creek Park"
                    event_venue = park_name_w_location
                else:
                    event_organizer = "National Park Service"
                event_venue = event_venue if event_venue else "See event website"
                if not event_description:
                    event_description = scrape_event_description(event_website)
                schematized_nps_event = {
                                            "Event Name":event_name,
                                            "Event Description":event_description,
                                            "Event Start Date":date,
                                            "Event Start Time":event_start_time,
                                            "Event End Date":date,
                                            "Event End Time":event_end_time,
                                            "All Day Event":event_all_day,
                                            "Event Venue Name":event_venue,
                                            "Event Organizers":event_organizer,
                                            "Timezone":'America/New_York',
                                            "Event Cost":event_cost,
                                            "Event Currency Symbol":"$",
                                            "Event Category":event_tags,
                                            "Event Website":event_website,
                                            "Event Featured Image":event_image
                                          }
                schematized_nps_events.append(schematized_nps_event)
    else:
        #TODO: when this occurs, it seems there's a discrepancy between the NPS API results
        #and what's displayed on an event's website. This might be an issue
        #to raise with the NPS API maintainers.
        logger.warning(f'This event did not have equal start and end dates: {nps_event}')
        schematized_nps_events = []

    return schematized_nps_events

def main():
    '''
    Returns NPS events for VA, DC and MD. Each event is a dict conforming to the wordpress schema.
    '''
    nps_events = get_nps_events()
    events = []
    for nps_event in nps_events:
        schematized_nps_events = schematize_nps_event(nps_event)
        events.extend(schematized_nps_events)

    return events


if __name__ == '__main__':
    events = main()