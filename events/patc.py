import logging
import posixpath
import requests

from bs4 import BeautifulSoup
from dateutil.parser import parse
import more_itertools as mi
import pandas as pd
import json
import re

URL_BASE = "https://www.patc.net/PATC/Calendar/PATC/"
CALENDAR_BASE_URL = ("Custom/Calendar.aspx?hkey" 
                     "=9fc06544-1c54-4a47-9efc-8fcd2420a646")
KEYWORDS = ["Start Time", "Start Date", "Event Category", "www"]
RENAME_MAP = {
    "all_day_event": "All Day Event",
    "currency": "Event Currency Symbol",
    "Description": "Event Description",
    "end_date": "Event End Date",
    "end_time": "Event End Time",
    "event_cost": "Event Cost",
    "event_organizers": "Event Organizers",
    "start_date": "Event Start Date",
    "start_time": "Event Start Time",
    "time_zone": "Timezone",
    "venue": "Event Venue Name",
    "www": "Event Website",
    "cost": "Event Cost"
}


def make_request_content(url_subpath):
    """Make a request to a URL and return the Soup contents

    :params str url_subpath:
        String denoting subpath of the path to retrieve data from

    :return:
        A soup containing information about the page requested

    :rtype:
        bs4.BeautifulSoup
    """
    parse_link = posixpath.join(URL_BASE, url_subpath)
    res = requests.get(parse_link)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, features="html.parser")
    return soup


def get_event_cost(event_cost_description):
    mulla = []
    lowered = event_cost_description.lower()
    currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
    event_costs = re.findall(currency_re, event_cost_description)
    n = len(event_costs)
    if n > 0:
        for a in event_costs:
            if "donation" not in lowered and "voluntary" not in lowered:
                event_cost = a.split(".")[0].replace("$", '')
                event_cost = ''.join(s for s in a if s.isdigit())
                mulla.append(event_cost)
            else:
                event_cost = ''
    if len(mulla) > 0:
        event_cost = max(mulla)
    else: 
        event_cost = ''
    return event_cost


def find_event_data(link):
    """Retrieve event data from the Calendar

    :param str link:
        String denoting link to event

    :return:
        A list of events

    :rtype:
        list
    """
    res = make_request_content(link)

    # there appears to be faulty calendar events that are unable to be parsed
    try:
        desc = ""
        long_string = "ctl01_TemplateBody_WebPartManager1_gwps" \
            "te_container_c1_cic1_DataList1_ctl01_IT_TR1_C2"
        for word in res.findAll("p"):
            desc = desc + word.text
        desc_td = res.find(
            "td", {"id": long_string})
        if desc_td is not None:
            desc = desc_td.getText().encode(
                "ascii", "ignore").decode().strip()
        else:
            desc = "See event website"
        results = {
            "Event Name": res.findAll("th")[-1].getText().strip(),
            # "Description": res.findAll("p")[-1].getText().strip(),
            "Description": desc,
            "Event Cost": get_event_cost(desc),

        }
    except IndexError:
        return

    for para in res.findAll("p"):
        if any([word + ":" in para.getText() for word in KEYWORDS]):
            logging.info("found event info: %s", para.getText().strip())
            header = mi.one(para.findAll("strong"))
            category, _, _ = header.getText().rpartition(":")
            value = mi.last(para.children)
            # sometimes BS4 will return NavigableString or some subclass
            # that appears to be string, we need to encode them to remove
            # non-ascii characters and then decode them from binary
            if not isinstance(value, str):
                value = value.getText()
            results[category] = value.encode(
                "ascii", "ignore").decode().strip()
    results["www"] = URL_BASE + link 
    return results


def format_df_time_columns(df):
    """Standalone function to format data in accordance to this structure:
    https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_schema.md

    :param pandas.DataFrame df:
        Dataframe to format

    :return:
        Formatted dataframe

    :rtype:
        pandas.DataFrame
    """
    cols_mapper = {
        "start_date": "Start Date",
        "start_time": "Start Time",
        "end_date": "Start Date",
    }

    for key, value in cols_mapper.items():
        if "date" in key:
            df[key] = df[value].apply(
                lambda x: parse(x).date().strftime('%Y-%m-%d'))
        else:
            df[key] = df[value].apply(
                lambda x: parse(x).strftime("%H:%M:%S"))
    return df


def main():
    records = []
    events = make_request_content(CALENDAR_BASE_URL)
    for event in events.findAll("a"):
        # impute empty string because you cannot 
        # do an equality check on NoneType
        event_link = event.attrs.get("href", "")
        if "calendar.aspx" in event_link:
            url = posixpath.split(
                event_link)[-1]
            logging.info("found calendar event, %s", url)
            data = find_event_data(posixpath.join("Custom", url))
            # there appears to be faulty 
            # calendar events that are unable to be parsed
            if data:
                records.append(data)
    data = pd.DataFrame.from_records(records)
    data = (
        data.assign(
            all_day_event=True,
            time_zone="America/New_York",
            end_time="23:59:59",
            # event_cost="Please refer to website",
            currency="$",
            venue="Please refer to website",
            event_organizers="Potomac Appalachian Trail Club",
        )
        .pipe(format_df_time_columns)
        .drop(["Start Date", "Start Time"], axis=1)
        .rename(columns=RENAME_MAP)
    )
    data = data.to_dict('records')
    return data


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    events = main()
    print(json.dumps(events, indent=4, sort_keys=True))