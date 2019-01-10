import requests
import os
import re
import json
import sys
import csv
import boto3

bucket = 'aimeeb-datasets-public'
is_local = False

# Be sure to create an env variable with the NPS API key. For example,
# $ export NPS_KEY=<NPS API Key>

try:
    NPS_KEY = os.environ['NPS_KEY']
except KeyError:
    print("Add your NPS_KEY as an env variable.")
    sys.exit(1)


def get_park_codes_by_state(state, limit = 200):
    '''
    Given a state (e.g. 'DC'), return all of its NPS park codes. These are used as params for the NPS events API
    Parameters:
        state (str): a two character string for a state abbreviation (eg. 'DC')
        limit (int): number of results to return per request. Default is 200.
    Returns:
        park_codes (list): a list of str 4-char park codes to be used with the NPS Events API
    '''

    key_param = f'&api_key={NPS_KEY}'
    limit_param = f'&limit={limit}'
    url = "https://developer.nps.gov/api/v1/parks?stateCode=" + state + key_param + limit_param
    r = requests.get(url)
    data = r.json()
    park_codes = []
    for park in data["data"]:
        park_codes.append(park["parkCode"])

    return park_codes

def get_park_events(park_code, limit=200):
    '''
    Get events data from the National Parks Service Events API for a given park_code
        
    Parameters:
        park_code (str): a park_code as returned by the NPS parkCode API through get_park_codes_by_state()
        limit (int): number of results to return per request. Default is 200
    
    Returns:
        park_events (list): A list of dicts representing each event with 'park' as the siteType. 
                            The dict structures follows that of the NPS Events API.
    '''

    park_code_param = f'?parkCode={park_code}'
    limit_param = f'&limit={limit}'
    key_param = f'&api_key={NPS_KEY}'
    url = "https://developer.nps.gov/api/v1/events"+park_code_param+limit_param+key_param
    r = requests.get(url)
    r_json = r.json()        
    data = r_json['data']
    park_events = []
    for d in data:
        if d['siteType'] == 'park':
            park_events.append(d)
    
    return park_events

def get_nps_events(park_codes):
    '''
    Get all of the events associated with a park code
    Parameters:
        park_codes (list): a list of str 4-char park codes.
    Returns:
        nps_events (list): a list of events
    '''
    
    nps_events = []
    for park_code in park_codes:
        try:
            park_events = get_park_events(park_code)
            if len(park_events) > 1:
                for park_event in park_events:
                    nps_events.append(park_event)
        except Exception as e:
            print(e)
       
    return nps_events

def get_park_geo_data(park_codes):
    '''
    Given a park_code, use the NPS Parks API to obtain geo and location data to match our application's schema
    Parameters:
        park_codes (list): a list of park codes as strings as returned by get_park_codes_by_state()
    Returns:
        park_codes_geo_map (dict): a dict containing both the geo and location objects to insert into an event's schema
    '''
    
    park_codes_geo_map = {k:None for k in park_codes}
    for park_code in park_codes:
        key_param = f'&api_key={NPS_KEY}'
        endpoint = "https://developer.nps.gov/api/v1/parks?parkCode=" + park_code + key_param + "&fields=addresses"
        r = requests.get(endpoint)
        data = r.json()['data']
        lat_lon = data[0]["latLong"]
        try:
            lat, lon = tuple([".".join(re.findall(r'\d+', x)) for x in lat_lon.split(",")])
        except ValueError:
            lat, lon = ('','')
        name = data[0]['name']
        description = data[0]['description']

        city = ''
        state = ''
        postal_code = ''
        street = ''
        for address in data[0]["addresses"]:
            if address["type"] == "Physical":
                city += address["city"]
                state += address["stateCode"]
                postal_code += str(address["postalCode"])
                street += address['line1'] + ' ' + address['line2'] + ' ' +address['line3']

        geo_obj = {'lat':lat,
                   'lon':lon}
        location_obj = {'streetAddress':street,
                        'addressLocality':city,
                        'addressRegion':None,
                        'postalCode':postal_code,
                        'addressCountry':'US',
                        'name':name,
                        'description':description,
                        'telephone':None} 
    
        park_codes_geo_map[park_code] = {'geo':geo_obj, 'location':location_obj, 'state':state}
    
    return park_codes_geo_map

def shcematize_nps_event(nps_event, park_codes_geo_map):
    '''
    Converts the event data from the NPS API into our application's schema.
    Parameters:
        nps_event (dict): a dict representing the json of a single NPS event.
        park_codes_geo_map (dict): a dict containing both the geo and location objects to insert into an event's schema
    Returns:
        event_id (str): unique identifier for this event
        schematized_nps_event (dict): the event data in our application's schema    
    '''
    
    event_id = nps_event['id']
    name = nps_event['title']
    startDate = nps_event['dateStart']
    endDate = nps_event['dateEnd']
    park_code = nps_event['siteCode']
    geo = park_codes_geo_map[park_code]['geo']
    state = park_codes_geo_map[park_code]['state']
    regResURL = nps_event['regResURL']
    infoURL = nps_event['infoURL']
    portalName = nps_event['portalName']
    if len(regResURL) > 0:
        url = regResURL
    else:
        r = requests.get(f"https://www.nps.gov/planyourvisit/event-details.htm?id={event_id}")
        if r.status_code == 404:
            if len(portalName) > 0:
                url = portalName
            else:
                url = infoURL
        else:
            url = f"https://www.nps.gov/planyourvisit/event-details.htm?id={event_id}"
    image = nps_event['images']
    description = nps_event['description']
    registrationRequired = True if nps_event['isRegResRequired'] else 0
    registrationByDate = nps_event['regResInfo']
    registrationURL = nps_event['regResURL']
    fee = 'free' if nps_event['isFree'] else nps_event['feeInfo']
    location = park_codes_geo_map[park_code]['location']
    organization = {'name':nps_event['organizationName'],
                    'description':None,
                    'url':None,
                    #'telephone':nps_event['contactTelephoneNumber'],
                    'email':nps_event['contactEmailAddress']}
    activityCategories = nps_event['tags']
    eventTypes = nps_event['types']
    ingested_by = 'https://github.com/DataKind-DC/capital-nature-ingest/tree/master/ingest_scripts/nps.py'
    #this is the old schema below
    '''
    schematized_nps_event = { 'name': name,
                              'startDate': startDate,
                              'endDate': endDate,
                              'geo': geo,
                              'url': url,
                              'image': image,
                              'description': description,
                              'registrationRequired': registrationRequired,
                              'registrationByDate': registrationByDate,
                              'registrationURL': registrationURL,
                              'fee': fee,
                              'location': location,
                              'organizationDetails': organization,
                              'offers':None,
                              'physicalRequirements':None,
                              'activityCategories':activityCategories,
                              'eventTypes':eventTypes,
                              'ingested_by':ingested_by}
    '''
    #here's the new schema
    venueAddress = f"{location['streetAddress']} {location['addressLocality']}, {state} {location['postalCode']}, USA"
    times = nps_event['times']
    #TODO handle multiple start and end times
    schematized_nps_event = [
                              {
                                "website": url, 
                                "startDate": startDate, 
                                "endDate": endDate, 
                                "startTime": None, 
                                "latitude": geo['lat'], 
                                "venueName": location['name'], 
                                "endTime": None, 
                                "longitude": geo['lon'], 
                                "venueAddress": venueAddress
                              }
                            ]

    return event_id, schematized_nps_event

def main():
    va_codes = get_park_codes_by_state('VA')
    dc_codes = get_park_codes_by_state('DC')
    md_codes = get_park_codes_by_state('MD')
    park_codes = set(va_codes + dc_codes + md_codes)
    nps_events = get_nps_events(park_codes)
    park_codes_geo_map = get_park_geo_data(park_codes)
    events = {}
    for nps_event in nps_events:
        event_id, schematized_nps_event = shcematize_nps_event(nps_event, park_codes_geo_map)
        events[event_id] = schematized_nps_event
    
    return events


def nps_handler(event, context):
    '''
    AWS lambda function for NPS events.
    '''
    _ = event['url']
    source_name = event['source_name']
    events = main()
    filename = '{0}-results.csv'.format(source_name)
    fieldnames = list(events[list(events.keys())[0]][0].keys())
    if not is_local:
        with open('/tmp/{0}'.format(filename), mode = 'w') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            for event_id in events:
                nps_event = events[event_id][0]
                writer.writerow(nps_event)
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file('/tmp/{0}'.format(filename), 
                                    bucket, 
                                    'capital-nature/{0}'.format(filename)
                                    )  


# For local testing
# event = {
#   'url': 'https://nps.gov',
#   'source_name': 'nps'
# }
# is_local = True
# nps_handler(handler(event, {}))