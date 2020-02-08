import logging
import re
import unicodedata
from urllib3.util.retry import Retry

from bs4 import BeautifulSoup
from dateutil import parser
import requests
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)


def requests_retry_session(retries=3, 
                           backoff_factor=0.3, 
                           status_forcelist=(429, 500, 502, 503, 504), 
                           session=None):
    '''
    Use to create an http(s) requests session that will retry a request.
    '''
    session = session or requests.Session()
    retry = Retry(
        total=retries, 
        read=retries, 
        connect=retries, 
        backoff_factor=backoff_factor, 
        status_forcelist=status_forcelist
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session


def get_description(soup):
    '''
    Clean up the event description
    :param soup: bs4 soup of the event detail page
    :return: cleaned description
    '''
    description_container = soup.find(
        "div",
        {"class": "eventitem-column-content"}
    )
    if not description_container:
        return ""
    description_parts = []
    for p in description_container.find_all("p"):
        parent_has_class = p.parent.has_attr("class")
        if parent_has_class and ("image-caption" in p.parent["class"]):
            # filter out image captions
            continue
        description_parts.append(unicodedata.normalize("NFKD", p.get_text()))
    if len(description_parts) == 0:
        return ""
    clean_description_parts = description_parts
    # strip photo credit
    if description_parts[0].strip().startswith("Photo: "):
        clean_description_parts = description_parts[1:]
    
    return " ".join(clean_description_parts)


def get_start_and_end_times(soup):
    '''
    Gets the start and end times of an event. Can vary depending on if it's a
    multiday event, so handle both cases here
    :param soup: bs4 soup of the detail page
    :return: tuple where first elt is start time and second is end time
    '''
    start_time, end_time = "", ""
    if soup.find("time", {"class": "event-time-12hr-start"}):
        start_time = soup.find("time", {"class": "event-time-12hr-start"}).text
        end_time = soup.find("time", {"class": "event-time-12hr-end"}).text
    else:
        times = soup.find_all("time", {"class": "event-time-12hr"})
        start_time = times[0].get_text()
        end_time = times[1].get_text()
    times = [start_time, end_time]
    return [parser.parse(t).strftime("%H:%M:%S") for t in times]


def get_category(soup):
    '''
    Get event category
    :param soup: bs4 soup of the detail page
    :return: the event category, or an empty string if we can't find it
    '''
    meta_info = soup.find_all("li", {"class": "eventitem-meta-item"})
    for meta in meta_info:
        meta_match = re.search("Posted in (.*)", meta.get_text())
        if meta_match:
            return meta_match.group(1)
    return ""


def get_featured_image(soup):
    '''
    Get featured image
    :param soup: bs4 soup of the detail page
    :return: the image src if present
    '''
    main_content = soup.find("div", {"class": "eventitem-column-content"})
    maybe_image = main_content.find("img", {"class": "thumb-image"})
    return "" if not maybe_image else maybe_image["data-src"]


def get_event_detail(url):
    '''
    Get information from event detail page
    :param url: link to event detail page
    :return: Dict of event detail information
    '''
    r = get_request_result(url)
    if not r:
        return None
    soup = BeautifulSoup(r.content, "html.parser")

    # get dates/times
    time_els = soup.find_all("time", {"class": "event-date"})
    dates = [d.get_text() for d in time_els]
    description = get_description(soup)
    start_time, end_time = get_start_and_end_times(soup)

    # get venue
    is_venue = soup.find(
        "span",
        {"class": "eventitem-meta-address-line--title"}
    )
    event_venue_name = "" if not is_venue else is_venue.get_text()

    # cost is tricky. There was only one non-free event when I wrote this 
    # scraper, and the cost was in the
    # event description. I don't know if this will be consistent in the future.
    # So here's an attempt to cover
    # the one example I saw:
    cost_match = re.search(r"\$(\d+) non-member", description)
    cost = "" if cost_match is None else cost_match.group(1)

    category = get_category(soup)
    featured_image = get_featured_image(soup)
    event = {
        "Event Description": description,
        "Event Start Date": parser.parse(dates[0]).strftime("%Y-%m-%d"),
        "Event Start Time": start_time,
        "Event End Date": parser.parse(dates[-1]).strftime("%Y-%m-%d"),
        "Event End Time": end_time,
        "All Day Event": False,
        "Event Venue Name": event_venue_name,
        "Event Cost": cost,
        "Event Currency Symbol": "$",
        "Event Category": category,
        "Event Featured Image": featured_image
    }
    return event


def clean_event_info(evt_info):
    '''
    Clean the event information
    :param evt_info: dict of event information
    :return: None. Mutates evt_info
    '''
    for key in evt_info:
        if type(evt_info[key]) is str:
            evt_info[key] = evt_info[key].strip()


def get_request_result(url):
    '''
    This website tends to throw 429 (Too Many Requests). Try to make a request 
    to `url`, and if it fails, wait and retry up to `num_retries` times
    :param url: url of the page to scrape
    :param num_retries: number of times to try to scrape the page
    :return: the request result
    '''
    try:
        r = requests_retry_session().get(url)
    except Exception as e:
        msg = f"{e} getting making GET request to {url}"
        logger.critical(msg, exc_info=True)
        return
    
    return r


def get_event_info():
    '''
    Get events from the list below the calendar on the calendar-view page
    :return: list of dicts of event information
    '''
    url = "http://audubonva.org/calendar-view"
    org = "Audubon Society of Northern Virginia"
    r = get_request_result(url)
    soup = BeautifulSoup(r.content, "html.parser")
    all_event_info = []
    summary_divs = soup.find_all("div", {"class": "summary-content"})
    for idx, event in enumerate(summary_divs):
        try:
            link_elt = event.find("a", {"class": "summary-title-link"})
            event_detail_link = "http://audubonva.org" + link_elt["href"]
            event_name = link_elt.get_text()

            # grab the event excerpt if it exists
            is_excerpt = event.find(
                "div",
                {"class": "summary-excerpt"}
            )
            
            event_excerpt = "" if not is_excerpt else is_excerpt.get_text()

            # get detail, then add info from the list view
            evt_info = get_event_detail(event_detail_link)
            if not evt_info:
                continue
            evt_info["Event Name"] = event_name
            evt_info["Event Excerpt"] = event_excerpt
            evt_info["Timezone"] = "America/New_York"
            evt_info["Event Organizers"] = org
            evt_info["Event Website"] = event_detail_link

            clean_event_info(evt_info)
            all_event_info.append(evt_info)
        except Exception as e:
            msg = f"{e}: failed to get event at index {idx}"
            logger.error(msg, exc_info=True)

    return all_event_info


def main():
    event_info = []
    try:
        event_info = get_event_info()
    except Exception as e:
        msg = f"{e}: failed to get event IDs."
        logger.error(msg, exc_info=True)
    return event_info


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
