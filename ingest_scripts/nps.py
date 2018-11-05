import requests
import os
import re
import json

# Be sure to set env variables first
# $ export ELASTICSEARCH_DOMAIN=<Domain>
# $ export NPS_KEY=<NPS API Key>

# You can verify them with
# $ printenv

ELASTICSEARCH_DOMAIN = os.environ['ELASTICSEARCH_DOMAIN']
NPS_KEY = os.environ['NPS_KEY']


def get_park_codes_by_state(state, limit = 200):
    '''
    Given a state (e.g. 'DC'), return all of its NPS park codes. These are used as params for the NPS events API

    Parameters:
        state (str): a two character string for a state abbreviation (eg. 'DC')

    Returns:
        park_codes (list): a list of park codes to be used with the NPS Events API
    '''

    # Configure API request
    key_param = f'&api_key={NPS_KEY}'
    limit_param = f'&limit={limit}'
    url = "https://developer.nps.gov/api/v1/parks?stateCode=" + state + key_param + limit_param
    r = requests.get(url)
    data = r.json()
    park_codes = []
    for park in data["data"]:
        park_codes.append(park["parkCode"])

    return park_codes


def get_park_geo_data(park_code):
    '''
    Given a park_code, use the NPS Parks API to obtain geo and location data to match our application's schema

    Parameters:
        park_code (str): a park code as returned by get_park_codes_by_state()

    Returns:
        park_code_geo_map (dict): a dict containing both the geo and location objects to insert into an event's schema
    '''
    
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
    
    park_code_geo_map = {park_code:{'geo':geo_obj, 'location':location_obj}}
    
    return park_code_geo_map


def get_nps_events(park_code, limit=100):
    '''
    Get events data from the National Parks Service Events API for a given park_code
        
    Parameters:
        park_code (str): a park_code as returned by the NPS parkCode API through get_park_codes_by_state()
        limit (int): number of results to return per request. Default is 100
    
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


def filter_park_event(park_events):
    '''
    Iterate through all dictionaries in the park_events array, flattening each to get the key:value pairs that will map to our schema

    Parameters:
        park_events (list): a list of nested dicts, with representing an event as returned by the NPS API
    
    Returns:
        filtered_park_events (list): a list of flattened dicts, each representing an event, with only our schema keys
    '''
    
    def recursive_items(dictionary):
        '''
        Recursively yield key:value pairs in a nested dictionary of unknown depth
        '''

        for key, value in dictionary.items():
            if type(value) is dict:
                yield from recursive_items(value)
            else:
                yield (key, value)
    
    nps_keys = ['dateStart', 'description', 'images', 
                'id', 'dateEnd', 'isRegResRequired', 'infoURL','regResURL',
                'title','regResInfo','location','tags','parkFullName', 'latitude',
                'longitude','organizationName','contactTelephoneNumber','contactEmailAddress']
    
    filtered_park_events = []
    for park_event in park_events:
        temp_dict = {k:None for k in nps_keys}
        for key, _ in recursive_items(park_event):
            if key in nps_keys:
                temp_dict[key] = park_event[key]
        filtered_park_events.append(temp_dict)
    
    return filtered_park_events


def get_organzation_data(filtered_park_event):
    '''
    Return the organizaiton object needed by our application's schema given a filtered_park_event

    Parameters:
        filtered_park_event (dict): a flattened dict representing a signle park event

    Returns:
        filtered_park_event (dict): a dict containing the organization object to insert into an event's schema
    '''
    organization_obj = {'name':None,
                        'description':None,
                        'url':None,
                        'telephone':None,
                        'email':None}
    for k in filtered_park_event:
        if k == 'organizationName':
            organization_obj['name'] = filtered_park_event[k]
        elif k == 'contactTelephoneNumber':
            organization_obj['telephone'] = filtered_park_event[k]
        elif k == 'contactEmailAddress':
            organization_obj['email'] = filtered_park_event[k]
    
    return organization_obj


def transform_event_data(filtered_park_event):
    '''
    Transform the filtered data so that each dict within the array matches our schema

    Parameters:
        filtered_park_event (dict): a dict representing a single event returned by the NPS API

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
    # this renames the NPS keys to our schema's names
    key_map = {'title':'name',
               'dateStart':'startDate',
               'dateEnd':'endDate',
               'images':'image',
               'description':'description',
               'infoURL':'url',
               'isRegResRequired':'registrationRequired',
               'regResURL':'registrationURL',
               'tags':'activityCategories'}
    
    for k in filtered_park_event:
        if k in key_map:
            if k == 'regResInfo':
                # TODO: need to parse date out of the regResInfo. Will likely need many re's as I haven't seen an example of their
                # dt format. Insert value as such:
                # schema['registrationByDate'] = extracted_date
                pass
            elif k == 'images':
                images = filtered_park_event[k]
                image_urls = []
                for image in images:
                    image_url = image['url']
                    # some urls are relative and not absolute. So we'll assume the domain is 'https://www.nps.gov'
                    if "http" not in image_url:
                        image_url = 'https://www.nps.gov'+image_url
                    image_urls.append(image_url)
                schema['image'] = " ".join(image_urls) #schema requires url to be a string for now
            else:
                renamed_k = key_map[k]
                schema[renamed_k] = filtered_park_event[k]
                
    return schema


def put_event(schema, event_id):
    '''
    Void function that puts an event into application's ELASTICSEARCH_DOMAIN

    Parameters:
        schema (dict): a dict representing a single event
        event_id (str): a uid for an event. Taken from the NPS API
    '''
    
    json_schema = json.dumps(schema)
    r = requests.put("{0}/capital_nature/event/{1}".format(ELASTICSEARCH_DOMAIN, event_id),
                     data=json_schema,
                     headers={'content-type':'application/json'})
    
    # TODO: handle errors



def main():
    '''
    Fetch events for VA, DC and MD national parkts using NPS APIs, transforming each to fit our schema.
    
    Returns:
        events (list): a list of dicts. Keys are unique event ids and values are dictionaries representing
                       an event in our team's schema.
    '''
    
    va_codes = get_park_codes_by_state('VA')
    dc_codes = get_park_codes_by_state('DC')
    md_codes = get_park_codes_by_state('MD')
    park_codes = set(va_codes + dc_codes + md_codes)
    events = []
    for park_code in park_codes:
        park_code_geo_map = get_park_geo_data(park_code)
        park_events = get_nps_events(park_code)
        filtered_park_events = filter_park_event(park_events)
        for filtered_park_event in filtered_park_events:
            schema = transform_event_data(filtered_park_event)
            schema['geo'] = park_code_geo_map[park_code]['geo']
            schema['location'] = park_code_geo_map[park_code]['location']
            schema['organization'] = get_organzation_data(filtered_park_event)
            event_id = filtered_park_event['id']
            events.append({event_id:schema})
            # TODO insert put_event() here
            # put_event(schema, event_id)
    
    return events

if __name__ == '__main__':
    events = main()

    

