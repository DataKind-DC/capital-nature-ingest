import requests
import extruct
from bs4 import BeautifulSoup
import json
import re
import pprint
from w3lib.html import get_base_url


# Use extrucrt library to extract microdata from schema.org */
pp = pprint.PrettyPrinter(indent=2)
page = requests.get("https://www.anacostiaws.org/event/129-new-event.html")
base_url = get_base_url(page.text, page.url)
# data = extruct.extract(page.text, base_url=base_url)
result_data = extruct.extract(page.text, base_url, syntaxes=['json-ld'], uniform=True)
filtered = []
for e in result_data['json-ld']:
    if e['@type'] == 'Event':
         filtered.append(e)
# TODO: check assumption that it's OK to take the first item with type=event
event_json = filtered[0]
pp.pprint(event_json)

key_list = ['name','description','url','startDate','endDate','latitude','longitude']
event_data = {k:None for k in key_list}
for k in event_json:
    if k in key_list:
        event_data[k] = event_json[k]
    if k == 'location':
        location_dict = event_json[k]
        for loc_k in location_dict:
            if loc_k == 'geo':
                geo_dict = location_dict[loc_k]
                for geo_k in geo_dict:
                    if geo_k in key_list:
                        print('in here',geo_dict[geo_k])
                        event_data[geo_k] = geo_dict[geo_k]
print(event_data)

# Use BeautifulSoup to scrape fields not available in schema.org microdata
soup = BeautifulSoup(page.content, 'html.parser')

# registration data
