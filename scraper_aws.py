import requests
import extruct
from bs4 import BeautifulSoup
import json
import re
import pprint
from w3lib.html import get_base_url
import os

def process_events(event_url):
    page = requests.get(event_url)
    # list of keys for the event_data dict
    key_list = ['name','description','url', 'image', 'startDate','endDate', \
        'geo', 'location', 'venue', 'organization',
        'activityCategory','registrationRequired', 'registrationURL', 'physicalRequirements']
    # create empty event dict
    event_data = {k:None for k in key_list}
    # Use extrucrt library to extract microdata from schema.org */
    base_url = get_base_url(page.text, page.url)
    result_data = extruct.extract(page.text, base_url, syntaxes=['json-ld'], uniform=True)
    filtered = []
    for e in result_data['json-ld']:
        if e['@type'] == 'Event':
             filtered.append(e)
    # TODO: check assumption that it's OK to take the first item with type=event
    event_json = filtered[0]
    # pp.pprint(event_json)

    # get name / description / url / startDate / endDate / image
    for k in event_json:
        if k in key_list:
            event_data[k] = event_json[k]
    # check name to see if event has been cancelled; if so return None
    if event_data['name'].find('CANCELLED') != -1:
        return None
    # get geo (lat/lon) / address
    event_data['geo'] = {}
    event_data['location'] = {}
    if 'location' in event_json:
        if 'name' in event_json['location']:
            event_data['venue'] = event_json['location']['name']
        if 'geo' in event_json['location']:
            event_data['geo']['lat'] = event_json['location']['geo']['latitude']
            event_data['geo']['lon'] = event_json['location']['geo']['longitude']
        if 'address' in event_json['location']:
            address_elements = event_json['location']['address']['name'].split(',')
            # TODO: make this address parsing more robust; currently not verifying existence of fields or the order of fields
            #       also potential problem with states with space in the name!
            #       good enough for now for this script (all events will be DC or Maryland) but not OK for long term
            # Minor robustness catch added; only process address if there are 4 elements.
            if len(address_elements) == 4:
                event_data['location']['streetAddress'] = address_elements[0]
                event_data['location']['addressLocality'] = address_elements[1].lstrip()
                event_data['location']['addressRegion'] = address_elements[2].lstrip().split(' ')[0].lstrip()
                event_data['location']['postalCode'] = address_elements[2].lstrip().split(' ')[1].lstrip()
                event_data['location']['addressCountry'] = address_elements[3].lstrip()
            # print(address_elements)
    # set organization
    event_data['organization'] = 'Anacostia Watershed Society'
    # TODO: add full organization{} data programmatically
    # TODO: (sooner) --- I commented this out because it was causing error when writing to elasticsearch
    # event_data['organization'] = {}
    # event_data['organization']['name'] = 'Anacostia Watershed Society'
    # event_data['organization']['url'] = 'https://www.anacostiaws.org/'
    # set ingested by
    # TODO: this script may move and may be renamed; adjust this line of code acordingly!
    event_data['ingested_by'] = 'https://github.com/DataKind-DC/capital-nature-ingest/blob/master/scraper_aws.py'

    # Use BeautifulSoup to scrape fields not available in schema.org microdata
    soup = BeautifulSoup(page.content, 'html.parser')

    # registrationRequired
    # physicalRequirements
    all_p = soup.find_all('p')
    save_next = 0
    saving_tag = ''
    event_data['registrationRequired'] = 0
    for p in all_p:
        for item in p:
            if save_next:
                # TODO: reassess this cleanup code; currently removing leading ':' and replacing '\xa0' (latin8 non-breaking space) with space
                event_data['physicalRequirements'] = item.strip(":").replace('\xa0',' ')
                save_next = 0
            if item.name == 'strong':
                if item.contents[0] == 'Physical Requirements':
                    save_next = 1
                    saving_tag = 'physicalRequirements'
                if item.contents[0] == 'Registration is required':
                    event_data['registrationRequired'] = 1

    # activityCategory
    activity_info = soup.find('a', class_='rs_cat_link')
    for item in activity_info:
        event_data['activityCategory'] = item

    # registrationURL
    if event_data['registrationRequired'] == 1:
        registration_info = soup.find('div', class_ = 'rsep_url')
        reg_a_info = registration_info.find('a')
        event_data['registrationURL'] = (reg_a_info.get('href'))
    # TODO: consult with AWS staff to determine robust method of obtaining registrationByDate
    #         only way to do it now is parsing the description text, don't wnat to do that until we know their patterns

    # TODO: consult with AWS staff to see if they ever have a fee for events
    # pp.pprint(event_data)
    return(event_data)

def write_to_elasticsearch(eventList):
    success_counter = 0
    # TODO: use OS env variable for this instead of hard-coding it
    elasticsearch_domain = 'https://search-capital-nature-beta-qx6lvr45s4sk4tmm67w6tfvph4.us-east-1.es.amazonaws.com'
    # TODO: is it better to bundle the writes, or do one-by-one liks this?
    for event in eventList:
        event_id = event['url'].split('/')[-1]
        r = requests.put(
          "{0}/capital_nature/event/{1}".format(elasticsearch_domain, event_id),
          data=json.dumps(event),
          headers = {'content-type': 'application/json'})
        # TODO: create more robust status checking and reporting - this is set up for one-by-one writing, and checking for success count of 1
        #       also - if there is an error it prints to screen; should write to error log
        result = r.json()
        if r.status_code == 200 or r.status_code == 201:
            print("wrote event",event['url'])
            success_counter += 1
        else:
            print("error encountered for event",event['url'])
            print(result)
            print(r.status_code)
    return success_counter
# ------------------------------------
pp = pprint.PrettyPrinter(indent=2)

# vars used for finding event URLs to be processed
# TODO: will need to adjust to multi-year handlig
base_url = 'https://www.anacostiaws.org/'
year = '2018'
start_month = 8
end_month = 12

# list for storing anacostia watershed society (aws) event dicts
aws_events = []

#loop through calendar months
for month in range(start_month,end_month,1):
    calendar_url = base_url + str(month).zfill(2) + '/' + year + '.html'
    print(calendar_url)
    eventURLs = []
    # find event URLs
    calendar_page = requests.get(calendar_url)
    soup = BeautifulSoup(calendar_page.content, 'html.parser')
    event_list = soup.find_all('a', class_ = 'rsttip rse_event_link ')
    for event in event_list:
        eventURLs.append(base_url + event.get('href'))
    # loop through event URLs
    for url in eventURLs:
        # call function to populate event_data
        print("processing",url)
        single_event = process_events(url)
        if single_event == None:
            # TODO: Add logic to remove an event from elasticsearch if it was cancelled
            print(url, 'was cancelled and will not be loaded')
        else:
            aws_events.append(single_event)

print("processed ", len(aws_events), " events.")
# write events to elasticsearch
num_written = write_to_elasticsearch(aws_events)
print("wrote ", num_written, " events.")
