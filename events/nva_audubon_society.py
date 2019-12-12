import logging
import re

from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)


def get_description(soup):
    '''
    Clean up the event description
    :param soup: bs4 soup of the event detail page
    :return: cleaned description
    '''
    description_container = soup.find("div", {"class": "eventitem-column-content"})
    if not description_container:
        return ""
    description_parts = [p.get_text() for p in description_container.find_all("p")]
    if len(description_parts) == 0:
        return ""
    clean_description_parts = description_parts
    # strip photo credit
    if description_parts[0].strip().startswith("Photo: "):
        clean_description_parts = description_parts[1:]
    return " ".join(clean_description_parts)


def get_start_and_end_times(soup):
    '''
    Gets the start and end times of an event. Start and end time locations can vary depending on whether it's a
    multiday event, so handle both cases here
    :param soup: bs4 soup of the detail page
    :return: tuple where first elt is start time and second is end time
    '''
    start_time, end_time = "", ""
    if soup.find("time", {"class": "event-time-12hr-start"}):
        start_time = soup.find("time", {"class": "event-time-12hr-start"}).get_text()
        end_time = soup.find("time", {"class": "event-time-12hr-end"}).get_text()
    else:
        times = soup.find_all("time", {"class": "event-time-12hr"})
        start_time = times[0].get_text()
        end_time = times[1].get_text()
    return start_time, end_time


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
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    dates = [d.get_text() for d in soup.find_all("time", {"class": "event-date"})]
    description = get_description(soup)
    start_time, end_time = get_start_and_end_times(soup)

    # get venue
    maybe_event_venue_name = soup.find("span", {"class": "eventitem-meta-address-line--title"})
    event_venue_name = "" if not maybe_event_venue_name else maybe_event_venue_name.get_text()

    # cost is tricky. There was only one non-free event when I wrote this scraper, and the cost was in the
    # event description. I don't know if this will be consistent in the future. So here's an attempt to cover
    # the one example I saw:
    cost_match = re.search(r"\$(\d+) non-member", description)
    cost = "" if cost_match is None else cost_match.group(1)

    category = get_category(soup)
    featured_image = get_featured_image(soup)


    return {
        "Event Description": description,
        "Event Start Date": dates[0],
        "Event Start Time": start_time,
        "Event End Date": dates[-1],
        "Event End Time": end_time,
        "All Day Event": False,
        "Event Venue Name": event_venue_name,
        "Event Cost": cost,
        "Event Currency Symbol": "$",
        "Event Category": category,
        "Event Featured Image": featured_image
    }


def clean_event_info(evt_info):
    '''
    Clean the event information
    :param evt_info: dict of event information
    :return: None. Mutates evt_info
    '''
    for key in evt_info:
        if type(evt_info[key]) is str:
            evt_info[key] = evt_info[key].strip()


def get_event_info():
    '''
    Retrieve the upcoming events from the list below the calendar on the calendar-view page
    :return: list of dicts of event information
    '''
    url = "http://audubonva.org/calendar-view"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    all_event_info = []

    for idx, event in enumerate(soup.find_all("div", {"class": "summary-content"})):
        try:
            link_elt = event.find("a", {"class": "summary-title-link"})
            event_detail_link = "http://audubonva.org"+link_elt["href"]
            event_name = link_elt.get_text()

            # grab the event excerpt if it exists
            maybe_event_excerpt = event.find("div", {"class": "summary-excerpt"})
            event_excerpt = "" if not maybe_event_excerpt else maybe_event_excerpt.get_text()

            # get detail, then add info from the list view
            evt_info = get_event_detail(event_detail_link)
            evt_info["Event Name"] = event_name
            evt_info["Event Excerpt"] = event_excerpt
            evt_info["Timezone"] = "America/New_York"
            evt_info["Event Organizers"] = "Audubon Society of Northern Virginia"
            evt_info["Event Website"] = event_detail_link

            clean_event_info(evt_info)
            all_event_info.append(evt_info)
        except Exception as e:
            logger.error(f"{e}: failed to retrieve Audubon Society of Northern Virginia event at index {idx}", exc_info=True)

    return all_event_info


def main():
    event_info = []
    try:
        event_info = get_event_info()
    except Exception as e:
        logger.error(f"{e}: failed to retrieve Audubon Society of Northern Virginia event IDs.", exc_info = True)
    print(event_info)
    return event_info


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
