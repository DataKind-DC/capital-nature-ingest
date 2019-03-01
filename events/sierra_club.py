import re
import requests
import json
from datetime import datetime
import unicodedata

url="https://www.sierraclub.org/sc/proxy?url=https://act.sierraclub.org/events/services/apexrest/eventfeed/ent/6300,5051&_=1548294791086"

def fetch_page(url):
    html_doc = requests.get(url).content
    return html_doc

def get_event_cost(event_cost_description):
    event_cost_description_lower = event_cost_description.lower()
    currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
    event_costs = re.findall(currency_re, event_cost_description)
    if len(event_costs) == 1 and "donation" not in event_cost_description_lower and "voluntary" not in event_cost_description_lower:
        event_cost = event_costs[0].split(".")[0].replace("$", '')
        event_cost = ''.join(s for s in event_cost if s.isdigit())
    else:
        event_cost = ''

    return event_cost

def schematize_event_time(event_time):
    '''
    Converts a time string like '1:30 pm' to 24hr time like '13:30:00'
    '''
    try:
        datetime_obj = datetime.strptime(event_time, "%I:%M %p")
        schematized_event_time = datetime.strftime(datetime_obj, "%H:%M:%S")
    except ValueError:
        schematized_event_time = ''

    return schematized_event_time


def encode_event_description(event_description):
    '''
    removes if there are any special characters in the description
    '''

    return unicodedata.normalize('NFKD', event_description)


def schematize_event_date(event_date):
    '''
    Converts a date like '2019-12-2' to '2019-12-02'
    '''
    try:
        datetime_obj = datetime.strptime(event_date, "%Y-%m-%d")
        schematized_event_date = datetime.strftime(datetime_obj, "%Y-%m-%d")
    except ValueError:
        schematized_event_date = ''

    return schematized_event_date


def handle_ans_page(events):
    events_list = []

    for event in events:
        events_data = {}
        events_data['Event Name'] = event.get('eventName','')
        events_data['Event Description'] = encode_event_description(event.get('description', ''))
        events_data['Event Start Date'] = schematize_event_date(event.get('startDate',''))
        events_data['Event Start Time'] = schematize_event_time(event.get('startTime',''))
        events_data['Event End Date'] = schematize_event_date(event.get('endDate',''))
        events_data['Event End Time'] = schematize_event_time(event.get('endTime',''))
        events_data['All Day Event'] = False
        events_data['Timezone'] = "America/New_York"
        events_data['Event Organizers'] = "Sierra Club"
        events_data['Event Cost'] = get_event_cost(event.get('cost','0'))
        events_data['Event Currency Symbol'] = "$"
        events_data['Event Category'] = event.get('eventCategory','')
        events_data['Event Website'] = event.get('urlToShare','')
        # commenting event show map, latitude and longitude fields for now as The WordPress Event plugin doesn't
        # expect these fields, but we might eventually use their Map plugin, which would need those geo fields
        # events_data['latitude'] = event.get('lat','')
        # events_data['longitude'] = event.get('lng','')
        # events_data['Event Show Map'] = event.get('showOnMap','')
        events_list.append(events_data)

    return events_list


def handler(event, context):
    url = event['url']
    source_name = event['source_name']
    page = fetch_page({'url': url})
    page = json.loads(page)
    events = handle_ans_page(page['eventList'])
    return events


def main():
    url = "https://www.sierraclub.org/sc/proxy?url=https://act.sierraclub.org/events/services/apexrest/eventfeed/ent/6300,5051&_=1548294791086"
    page = fetch_page(url)
    page = json.loads(page)
    events = handle_ans_page(page['eventList'])
    return events


if __name__ == '__main__':
    events = main()