import requests
import os
import json

ELASTICSEARCH_DOMAIN = os.environ['ELASTICSEARCH_DOMAIN']

# Eventbrite API Auth token - available at https://www.eventbrite.com/account-settings/apps
EVENTBRITE_TOKEN = os.environ['EVENTBRITE_TOKEN']

class GenericEventbriteIngester:
    '''
    Create a new instance with:
    >>> ingester = GenericEventbriteIngester(12345)

    where the argument is the organizer_id of the Eventbrite organizer.

    Then execute as:
    >>> ingester.run()

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
                    'https://github.com/DataKind-DC/capital-nature-ingest/tree/master/ingest_scripts/national_arboretum_eventbrite.py',
                'handler': self.handle_fixed},
        }

    def get_eventbrite_url(self, endpoint, endpoint_params={}, get_params={'token': EVENTBRITE_TOKEN}):
        eventbrite_api_base_url = 'https://www.eventbriteapi.com/v3'
        print(endpoint_params)
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

    def run(self):
        events_url = self.get_eventbrite_url(
            '/events/search/',
            get_params = {'token': EVENTBRITE_TOKEN, 'organizer.id': self.org_id})
        self.all_events = requests.get(events_url).json()['events']
        self.parse_events()
        self.upload_events()

    def upload_events(self):
        for event in self.output_data.keys():
            print('Uploading ', event)
            r = requests.put(
                "{0}/capital_nature/event/{1}".format(ELASTICSEARCH_DOMAIN, event),
                data=json.dumps(self.output_data[event]),
                headers={'content-type': 'application/json'})
            print('Result:', r.status_code)