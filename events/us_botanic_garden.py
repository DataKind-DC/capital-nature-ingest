import copy
import datetime
import json
import logging
import os
import re

from bs4 import BeautifulSoup
import requests

from .utils.log import get_logger

logger = get_logger(os.path.basename(__file__))


def get_event_ids(num_months):
    '''
    The US Botanic Garden calendar shown at
    https://www.usbg.gov/programs
    is populated by JSON returned by DoubleKnot's server on page load.

    This function makes that request `num_months` times, with different 
    start offsets, to retrieve `num_months` worth of
    event IDs. The IDs are used in `get_event_info` to create event detail URLs
    URL in `get_event_info`.

    :param num_months: number of months to get data for - should be an int > 0
    :return: set of event ids
    '''
    req_params = (
        ("calendarid", "dkdpm"),
    )
    # Most of these parameters are copied directly from the request that 
    # ran when the calendar loaded in
    # my browser. Even changing "visibleEnd" to greater than a month out 
    # seems to only retrieve a month's worth
    # of data, so we will run the request with a start date offset from 
    # the first of today's month from
    # 0 to num_months - 1
    base_req_data = {
        "action": "Init",
        "header": {
            "control": "dpm",
            "id": "DKdpm",
            "v": "218-lite",
            "visibleStart": None,
            "visibleEnd": "9999-12-31T23:59:59",
            "startDate": None,
            "reqStartDate": "9999-12-31T23:59:59",
            "reqEndDate": "9999-12-31T23:59:59",
            "orgKey": 4153,
            "orgList": "4153",
            "categoryList": "",
            "reserveOptionsList": "",
            "headerBackColor": "#F3F3F9",
            "backColor": "#ffffff",
            "nonBusinessBackColor": "#ffffff",
            "timeFormat": "Auto",
            "weekStarts": 0
        }
    }
    # `seen_event_ids` needs to be a set since sometimes the request
    # returns overlapping events from adjacent months
    # (these are used to pad the start and end of the calendar view)
    seen_event_ids = set()
    today = datetime.datetime.now()
    base_month = today.month
    base_year = today.year
    for month_offset in range(num_months):
        req_data = copy.deepcopy(base_req_data)
        # request all events starting from the first of the current month,
        # even if the current date is later,
        # so users can see entire month's history if needed
        curr_year = base_year
        curr_month = month_offset + base_month
        if curr_month > 12:
            curr_year += int(curr_month / 12)
            curr_month = curr_month % 12
        first_of_month = f"{curr_year}-{curr_month}-01T00:00:00"
        req_data["header"]["visibleStart"] = first_of_month
        req_data["header"]["startDate"] = first_of_month
        # doubleknot require the word "JSON" to be prepended to the 
        # stringified JSON data
        response = requests.post(
            'https://usbg.doubleknot.com/app/calendar/eventdata',
            params=req_params,
            data="JSON" + json.dumps(req_data))
        
        for evt in response.json()["Events"]:
            seen_event_ids.add(evt["id"])

    # return in order of id
    return sorted(list(seen_event_ids))


def get_cost(soup):
    cost_span = soup.find("span", {"id": "lblCost"})
    cost = "0"
    if cost_span is not None:
        maybe_cost = cost_span.get_text().lower()
        m = re.search(r"([0-9\.]+) per non-?member", maybe_cost)
        try:
            cost = m.group(1)
        except AttributeError:
            cost = ''

    return cost


def get_event_info(evt_id):  # noqa: C901
    '''
    Given an event id, go to the event detail page and extract all its info
    :param evt_id: id of event, used in event detail page url
    :return: dict of event information
    '''
    url = (
        "https://usbg.doubleknot.com/registration/calendardetail.aspx"
        f"?activitykey={evt_id}&orgkey=4153"
    )
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    # get cost. Since we can only provide one, use the non-member cost
    cost = get_cost(soup)

    # get schedule info
    startdt = soup.find("time", {"id": "timeStartTime"})["content"]
    start_date, start_time_with_zone = startdt.split("T")
    start_time = start_time_with_zone.split("-")[0]
    enddt = soup.find("span", {"id": "lblEventDate"})["content"]
    end_date, end_time_with_zone = enddt.split("T")
    end_time = end_time_with_zone.split("-")[0]

    # get the rest of the info, which unfortunately is embedded in a 
    # sequence of p elements without identifiers
    # except the content and position
    img_host = (
        "https://5a6a246dfe17a1aac1cd-b99970780ce78ebdd694d83e551ef810"
        ".ssl.cf1.rackcdn.com/"
    )
    desc, featured_image, venue, evt_name, evt_category = "", "", "", "", ""
    # there is only one element in divNotes with class dk_cd_itemdetail
    div_notes = soup.find("div", {"id": "divNotes"})
    right_panel = div_notes.find("div", {"class": "dk_cd_itemdetail"})

    for idx, p in enumerate(right_panel.find_all("p")):
        text = p.get_text().replace("\n", " ").strip()
        images = p.find_all("img")
        if len(images) > 0:
            featured_image = img_host + images[0]["src"]
        elif text.startswith("LOCATION:"):
            venue = text.split("LOCATION:")[1].strip()
        elif idx == 0:
            # I thought I could get the evt name and category from the th with
            # class dk-title-bar, but it's not
            # formatted consistently. The fist p element is, 
            # like this - CATEGORY: TITLE
            title_re = re.search(r"^([^:]+):\s*(.*)", text)
            try:
                evt_category = title_re.group(1)
            except AttributeError:
                evt_category = ''
            evt_name = title_re.group(2)
        elif idx == 1:
            # it's the subtitle - skip it
            continue
        elif not re.search("^[A-Z- ]+:", text):
            # Add all text that doesn't start with some kind of label and 
            # isn't the subtitle to the desc
            desc += text + "\n"

    evt_info = {
        "Event Name": evt_name.title(),
        "Event Description": desc,
        "Event Start Date": start_date,
        "Event Start Time": start_time,
        "Event End Date": end_date,
        "Event End Time": end_time,
        "All Day Event": False,
        "Timezone": "America/New_York",
        "Event Venue Name": "United States Botanic Garden: " + venue,
        "Event Organizers": "United States Botanic Garden",
        "Event Cost": cost,
        "Event Currency Symbol": "$",
        "Event Category": evt_category.title(),
        "Event Website": url,
        "Event Featured Image": featured_image
    }

    # make sure the values are cleaned up
    for key in evt_info:
        if type(evt_info[key]) is str:
            evt_info[key] = evt_info[key].replace("\xa0", " ").strip()

    return evt_info


def main():
    # retrieve event IDs
    event_ids = []
    try:
        event_ids = get_event_ids(6)
    except Exception as e:
        msg = f"Exception getting US Botanic Garden event IDs: {e}"
        logger.error(msg, exc_info=True)

    # retrieve event information
    event_info = []
    for evt_id in event_ids:
        try:
            event_info.append(get_event_info(evt_id))
        except Exception as e:
            msg = f"{e}: failed to get event info for {evt_id}."
            logging.exception(msg, exc_info=True)
    
    return event_info


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
