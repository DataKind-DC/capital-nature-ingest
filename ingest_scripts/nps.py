import requests
import os
import geocoder
import json
from datetime import datetime
import pprint

# Be sure to set env variables first
# $ export ELASTICSEARCH_DOMAIN=<Domain>

# You can verify them with
# $ printenv

def get_park_names_by_state(state):
    '''
    Given a state (e.g. 'DC'), return all of its NPS park codes. These will be used as params for the NPS events API

    Parameters:
        state (str): a two character string for a state abbreviation (eg. 'DC')

    Returns:
        park_codes (list): a list of park codes to be used with the NPS Events API
    '''

    # Configure API request
    url = "https://api.nps.gov/api/v1/parks?stateCode=" + state
    r = requests.get(url)
    data = r.json()
    park_codes = []
    for park in data["data"]:
        park_codes.append(park["parkCode"])

    return park_codes


def get_nps_events():
    '''
    Get events data from the National Parks Service Events API for VA, DC and MD
    documentation: https://www.nps.gov/subjects/developer/api-documentation.htm#/events/getEvents
        
    Parameters:
        limit (int): number of results to return per request. Default is 50
    
    Returns:
        park_events (list): A list of dicts representing each event with 'park' as the siteType. 
                            The dict structures follows that of the NPS Events API.
    '''

    url = "https://api.nps.gov/api/v1/events?stateCode=DC&stateCode=VA&stateCode=MD&limit=600"
    r = requests.get(url)
    r_json = r.json()        
    data = r_json['data']
    park_events = []
    for d in data:
        if d['siteType'] == 'park':
            park_events.append(d)
    print(f"Done fetching data for {len(park_events)} events from NPS API.")
    
    return park_events

def recursive_items(dictionary):
    '''
    Recursively yield key:value pairs in a nested dictionary of unknown depth
    '''
    
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_items(value)
        else:
            yield (key, value)


def filter_data(data):
    '''
    Iterate through all dictionaries in the data array, flatting each and getting the key:value pairs that will map to our schema

    Parameters:
        data (list): a list of nested dicts for each event as returned by the NPS API
    
    Returns:
        filtered_data (list): a list of flattened dicts with only our schema keys for each event as returned by the NPS API
    '''
    
    nps_keys = ['dateStart', 'description', 'images', 
                'id', 'dateEnd', 'isRegResRequired', 'infoURL','regResURL',
                'title','regResInfo','location','tags','parkFullName', 'latitude',
                'longitude','organizationName','contactTelephoneNumber','contactEmailAddress']
    filtered_data = []
    for d in data:
        temp_dict = {k:None for k in nps_keys}
        for key, _ in recursive_items(d):
            if key in nps_keys:
                temp_dict[key] = d[key]
        filtered_data.append(temp_dict)
    
    return filtered_data

def transform_event_data(event_data):
    '''
    Transform the filtered data so that each dict within the array matches our schema

    Parameters:
        event_data (dict): a dict representing a single event returned by the NPS API

    Returns:
        schema (dict): a dict representing a single event that conforms to our schema
    '''
    # TODO: consider defining schema in a config file and then importing across all ingest scripts
    schema = {'name':None,
              'startDate':None,
              'endDate':None,
              'geo':None,
              'url':None,
              'image':None,
              'description':None,
              'registrationRequired':None,
              'registrationByDate':None,
              'registrationURL':None,
              'fee':None,
              'location':None,
              'organization':None,
              'offers':{'price':None,
                        'url':None},
              'physicalRequirements':None,
              'activityCategories':None,
              'eventTypes':None,
              'ingested_by':'https://github.com/DataKind-DC/capital-nature-ingest/tree/master/ingest_scripts/nps.py'}
    # to rename the NPS keys to fit our schema names
    key_map = {'title':'name',
               'dateStart':'startDate',
               'dateEnd':'endDate',
               'images':'image',
               'description':'description',
               'infoURL':'url',
               'isRegResRequired':'registrationRequired',
               'regResURL':'registrationURL',
               'tags':'activityCategories'}
    
    location = event_data['location']
    parkFullName = event_data['parkFullName']
    # TODO: only fetch geo data if needed (roughly 50% need the look up)
    location_obj, geo_obj = fetch_geo_and_location_objs(location, parkFullName)
    schema['geo'] = geo_obj
    schema['location'] = location_obj
    organization_obj = {'name':None,
                        'description':None,
                        'url':None,
                        'telephone':None,
                        'email':None}
    
    for k in event_data:
        if k in key_map:
            if k == 'regResInfo':
                # TODO: need to parse date out of the regResInfo. Will likely need many re's as I haven't seen an example of their
                # dt format. Insert value as such:
                # schema['registrationByDate'] = extracted_date
                pass
            elif k == 'images':
                images = event_data[k]
                image_urls = []
                for image in images:
                    image_url = image['url']
                    # some urls are relative and not absolute. So we'll assume the domain is 'https://www.nps.gov'
                    if "http" not in image_url:
                        image_url = 'https://www.nps.gov'+image_url
                    image_urls.append(image_url)
                schema['image'] = " ".join(image_urls) #schema requires url to be a string
            else:
                renamed_k = key_map[k]
                schema[renamed_k] = event_data[k]
        else:
            if k == 'organizationName':
                organization_obj['name'] = event_data[k]
            elif k == 'contactTelephoneNumber':
                organization_obj['telephone'] = event_data[k]
            elif k == 'contactEmailAddress':
                organization_obj['email'] = event_data[k]
                
    schema['organization'] = organization_obj

    return schema
            

def fetch_geo_and_location_objs(location, parkFullName):
    location_obj = {'streetAddress':None,
                    'addressLocality':None,
                    'addressRegion':None,
                    'postalCode':None,
                    'addressCountry':None,
                    'name':None,
                    'description':None,
                    'telephone':None} #doesn't exist in mapquest or NPS API
    geo_obj = {'lat':None,
               'lon':None}
    # TODO Make this work.
    g = geocoder.osm(location + ' ' + parkFullName + ' ' + 'Washignton, DC')
    g_json = g.json
    if g_json:
        geo_obj['lat'] = g_json['lat']
        geo_obj['lon'] = g_json['lng']
        location_obj['streetAddress'] = g_json['address']
        location_obj['addressCountry'] = 'US'
    else:
        pass  
    location_obj['name'] = location
    location_obj['description'] = parkFullName

    return location_obj, geo_obj


def put_event(schema):
    ELASTICSEARCH_DOMAIN = os.environ['ELASTICSEARCH_DOMAIN']
    event_id = schema['id']
    json_schema = json.dumps(schema)
    r = requests.put("{0}/capital_nature/event/{1}".format(ELASTICSEARCH_DOMAIN, event_id),
                     data=json_schema,
                     headers={'content-type':'application/json'})
    r.raise_for_status()


def main(write_json = False):
    '''
    Fetch events from the NPS API, transforming each event's json to match our schema before putting into ES.
    Optionally write the json as well.

    Parameters:
        write_json (bool): boolean flag to write json data into current working directory

    Returns
        filtered_data (list): list of event data matching our schema
    '''
    
    park_events = get_nps_events()
    filtered_data = filter_data(park_events)
    for i, event_data in enumerate(filtered_data):
        schema = transform_event_data(event_data)
        filtered_data[i] = schema
        put_event(schema)

    if write_json:
        now = datetime.now()
        file_name = 'nps_events_' + str(now)
        with open(file_name, 'w') as f:
            json.dump(filtered_data, f)

    return filtered_data



if __name__ == '__main__':
    filtered_data = main(write_json = False)

    

