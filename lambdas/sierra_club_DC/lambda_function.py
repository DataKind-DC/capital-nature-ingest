import boto3
import bs4
import csv
import re
import requests
import json
from datetime import datetime
import unicodedata
import pprint

bucket = 'aimeeb-datasets-public'
is_local = False
# The value ent/6300,5015 is hardcoded in the html and the last numeric part might be unix timestamp
url="https://www.sierraclub.org/sc/proxy?url=https://act.sierraclub.org/events/services/apexrest/eventfeed/ent/6300,5051&_=1548294791086"


def fetch_page(options):
    url = options['url']
    html_doc = requests.get(url).content
    return html_doc


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
        organizer_list = event.get('leaderList','')
        if(organizer_list):
            names = ""
            for organizer in  organizer_list:
                if(names != ""):
                    names += ","
                names += organizer.get('name','')

            events_data['Event Organizers'] = names
        else:
            events_data['Event Organizers'] = ""
        events_data['Event Cost'] = event.get('cost','0')
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
    # soup = bs4.BeautifulSoup(page, 'html.parser')
    event_output = handle_ans_page(page['eventList'])
    pprint.pprint(event_output)
    # filename = '{0}-results.csv'.format(source_name)
    # if not is_local:
    #     with open('/tmp/{0}'.format(filename), mode = 'w') as f:
    #         writer = csv.DictWriter(f, fieldnames = event_output[0].keys())
    #         writer.writeheader()
    #         [writer.writerow(event) for event in event_output]
    # s3 = boto3.resource('s3')
    # s3.meta.client.upload_file(
    #   '/tmp/{0}'.format(filename),
    #   bucket,
    #   'capital-nature/{0}'.format(filename)
    # )
    # return json.dumps(event_output, indent=2)
    return


# For local testing
event = {
  'url': url,
  'source_name': 'sierra_club_DC'
}
# is_local = False
print(handler(event, {}))
