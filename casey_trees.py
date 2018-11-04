import bs4
import json
import os
import requests
import extruct
import pprint
from w3lib.html import get_base_url

# establish elastic search
elasticsearch_domain = os.environ['ELASTICSEARCH_DOMAIN']

# setup pretty printer
pp = pprint.PrettyPrinter(indent=2)

# create request to get data from Casey Trees calendar
months = map(lambda m: "2018-{0}".format(m), range(10,13))
activityCategories = ['Tree Planting', 'Park Inventory', 'Tree Identification']

for month in months:
  r = requests.get("https://caseytrees.org/events/{0}/".format(month))
  base_url = get_base_url(r.text, r.url)
  data = extruct.extract(r.text, base_url = base_url, syntaxes=['json-ld'], uniform=True)

  # get json-ld data for Casey Trees
  event_json = []
  for jsonLD in data['json-ld']:
      if jsonLD['@type'] == 'Event':
          event_json.append(jsonLD)


  for individual_event in event_json:
    # establish list of properties in dict
    key_list = [
      'name',
      'startDate',
      'endDate',
      'geo',
      'url',
      'image',
      'description',
      'registrationRequired',
      'registrationByDate',
      'registrationURL',
      'fee',
      'location',
      'organization',
      'offers',
      'physicalRequirements',
      'activityCategory'
    ]
    
    event_data = {k:None for k in key_list}

    for k in individual_event:
      # if property from keylist exists within the event_json object, set property
      if k in key_list:
        event_data[k] = individual_event[k]

      event_data['geo'] = {}
      # Prevent key errors
      if 'location' in individual_event and 'geo' in individual_event['location']:
        event_data['geo']['lat'] = individual_event['location']['geo']['latitude']
        event_data['geo']['lon'] = individual_event['location']['geo']['longitude']
    
    for cat in activityCategories:
      if cat in individual_event['name']: event_data['activityCategory'] = cat 

    event_data['ingested_by'] = 'https://github.com/DataKind-DC/capital-nature-ingest/blob/master/casey_trees.py'

    # check each url to determine if event is duplicate
    event_id = filter(None, event_data['url'].split('/'))[-1]

    # create the request to submit data to elasticsearch
    r = requests.put(
      "{0}/capital_nature/event/{1}".format(elasticsearch_domain, event_id),
      data=json.dumps(event_data),
      headers = {'content-type': 'application/json'})

    # print status code
    # TODO: handle response, provide error messaging if necessary
    pp.pprint(r.status_code)