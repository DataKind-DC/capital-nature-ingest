import requests
import json
import csv
import boto3
import os
import datetime


bucket = 'aimeeb-datasets-public'
is_local = False
EVENTBRITE_TOKEN = os.environ['EVENTBRITE_TOKEN']
FONA_EVENTBRITE_ORG_ID = 13276552841


class EventbriteIngester:
    '''
    Create a new instance with:
    >>> ingester = EventbriteIngester(12345)

    where the argument is the organizer_id of the Eventbrite organizer.

    Then execute as:
    >>> ingester.scrape()

    which will pull that organizer's events from the Eventbrite API and PUT them to the Elasticsearch instance
    '''

    def __init__(self, org_id):
        self.org_id = org_id
        self.org_data = {}
        self.venues = {}
        self.output_data = {}
        self.field_handlers = {
            'name': {'keys': ['name', 'text'], 'handler': self.handle_simple},
            'startDate': {'keys': ['start'], 'handler': self.handle_date},
            'endDate': {'keys': ['end'], 'handler': self.handle_date},
            'geo': {'keys': ['venue_id'], 'handler': self.handle_geo},
            'url': {'keys': ['url'], 'handler': self.handle_simple},
            'image': {'keys': ['logo', 'url'], 'handler': self.handle_simple},
            'location': {'keys': ['venue_id'], 'handler': self.handle_location},
            'description': {'keys': ['description', 'text'], 'handler': self.handle_simple},
            'registrationRequired': {'keys': 1, 'handler': self.handle_fixed},
            'registrationURL': {'keys': ['url'], 'handler': self.handle_simple},
            # 'fee': {}, # TODO: handle this field
            'organizationDetails': {'keys': [org_id], 'handler': self.handle_org},
            'ingested_by': {
                'keys':
                    'https://github.com/DataKind-DC/capital-nature-ingest/tree/master/lambdas/fona/lambda_function.py',
                'handler': self.handle_fixed},
        }

    def get_eventbrite_url(self, endpoint, endpoint_params={}, get_params={'token': EVENTBRITE_TOKEN}):
        eventbrite_api_base_url = 'https://www.eventbriteapi.com/v3'
        endpoint = endpoint.format(**endpoint_params)
        get_args = ''.join([key + '=' + str(get_params[key]) + '&' for key in get_params.keys()])
        return eventbrite_api_base_url + endpoint + '?' + get_args

    def handle_simple(self, event, keys):
        if len(keys) == 1:
            return event[keys[0]]
        elif len(keys) == 2:
            return event[keys[0]][keys[1]]
        else:
            raise Exception("Can't handle more than 2 levels...")

    def handle_date(self, event, keys):
        return event[keys[0]]['utc']

    def handle_geo(self, event, keys):
        self.load_venue(event[keys[0]])
        return {
            'lat': self.venues[event[keys[0]]]['address']['latitude'],
            'lon': self.venues[event[keys[0]]]['address']['longitude']
        }

    def handle_location(self, event, keys):
        id = event[keys[0]]
        self.load_venue(id)
        return {
            'name': self.venues[id]['name'],
            'streetAddress': self.venues[id]['address']['address_1'],
            'addressLocality': self.venues[id]['address']['city'],
            'addressRegion': self.venues[id]['address']['region'],
            'postalCode': self.venues[id]['address']['postal_code']
        }

    def handle_fixed(self, event, val):
        return val

    def handle_org(self, event, keys):
        if len(self.org_data.keys()) == 0:
            api_url = self.get_eventbrite_url('/organizers/{id}/', endpoint_params={'id': keys[0]})
            org_json = requests.get(api_url).json()
            self.org_data = {
                'name': org_json['name'],
                'url': org_json['website'],
                'description': org_json['description']['text']
            }
        return self.org_data

    def load_venue(self, venue_id):
        if venue_id not in self.venues.keys():
            api_url = self.get_eventbrite_url('/venues/{id}/', endpoint_params={'id': venue_id})
            venue_json = requests.get(api_url).json()
            self.venues[venue_id] = venue_json

    def parse_events(self):
        for event in self.all_events:
            event_data = {}
            for field in self.field_handlers:
                event_data[field] = self.field_handlers[field]['handler'](event, self.field_handlers[field]['keys'])
            self.output_data[event['id']] = event_data

    def scrape(self):
        events_url = self.get_eventbrite_url(
            '/events/search/',
            get_params = {'token': EVENTBRITE_TOKEN, 'organizer.id': self.org_id})
        page = requests.get(events_url).json()
        self.all_events = page['events']
        self.parse_events()

def fetch_page(options):
    url = options['url']
    html_doc = requests.get(url).content
    return html_doc

# Create an EventbriteParser object, parse API, and convert to
def handle_fona_eventbrite_api():
    fona_ingester = EventbriteIngester(FONA_EVENTBRITE_ORG_ID)
    fona_ingester.scrape()
    event_output = []
    for e in fona_ingester.output_data.keys():
        data = fona_ingester.output_data[e]
        start = datetime.datetime.strptime(data['startDate'], '%Y-%m-%dT%H:%M:%SZ')
        end = datetime.datetime.strptime(data['endDate'], '%Y-%m-%dT%H:%M:%SZ')
        event_data = {
          'website': data['url'],
          'startDate': start.strftime('%Y-%m-%d'),
          'startTime': start.strftime('%I:%M %p'),
          'endDate': end.strftime('%Y-%m-%d'),
          'endTime': end.strftime('%I:%M %p'),
          'venueName': data['location']['name'],
          'venueAddress': f"{data['location']['streetAddress']} {data['location']['addressLocality']}, {data['location']['addressRegion']} {data['location']['postalCode']}, USA",
          'latitude': float(data['geo']['lat']),
          'longitude': float(data['geo']['lon'])
        }
        event_output.append(event_data)
    return event_output

def handler(event, context):
    url = event['url']
    source_name = event['source_name']
    page = fetch_page({'url': url})
    event_output = handle_fona_eventbrite_api()
    filename = '{0}-results.csv'.format(source_name)
    if not is_local:
        with open('/tmp/{0}'.format(filename), mode = 'w') as f:
            writer = csv.DictWriter(f, fieldnames = event_output[0].keys())
            writer.writeheader()
            [writer.writerow(event) for event in event_output]
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(
            '/tmp/{0}'.format(filename),
            bucket,
            'capital-nature/{0}'.format(filename)
        )
    else:
        with open('{0}'.format(filename), mode = 'w') as f:
            writer = csv.DictWriter(f, fieldnames = event_output[0].keys())
            writer.writeheader()
            [writer.writerow(event) for event in event_output]
    return json.dumps(event_output, indent=2)

# For local testing
# if __name__=="__main__":
#     event = {
#         'url': f'https://www.eventbriteapi.com/v3/events/search/?token={EVENTBRITE_TOKEN}&organizer.id={FONA_EVENTBRITE_ORG_ID}&',
#         'source_name': 'fona'
#     }
#     is_local = True
#     print(handler(event, {}))
