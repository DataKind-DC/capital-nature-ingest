import bs4
import requests
import json
import csv
import boto3

bucket = 'aimeeb-datasets-public'
is_local = False

def fetch_page(options):
  url = options['url']
  html_doc = requests.get(url).content
  return html_doc

# Given a beautiful soup object, return a list of events on that page
def handle_ans_page(soup):
  events = soup.find_all('div', {'class': 'event'})
  event_output = []
  for e in events:
    latLong = e.find('p').find('span', {'class': 'evcal_desc'})['data-latlng'].split(',')
    spanTime = e.find('p').find('span', {'class': 'evo_time'})
    event_data = {
      'website': e.find('a')['href'],
      'startDate': e.find('time', {'itemprop': 'startDate'})['datetime'],
      'startTime': spanTime.find('span', {'class': 'start'}).text,
      'endDate': e.find('time', {'itemprop': 'endDate'})['datetime'],
      'endTime': spanTime.find('span', {'class': 'end'}).text.replace('- ', ''),
      'venueName': e.find('span', {'itemprop': 'name'}).text,
      'venueAddress': e.find('item', {'itemprop': 'streetAddress'}).text,
      'latitude': float(latLong[0]),
      'longitude': float(latLong[1])
    }
    event_output.append(event_data)
  return event_output

def handler(event, context):
  url = event['url']
  source_name = event['source_name']
  page = fetch_page({'url': url})
  soup = bs4.BeautifulSoup(page, 'html.parser')
  event_output = handle_ans_page(soup)
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
  return json.dumps(event_output, indent=2)

# For local testing
# event = {
#   'url': 'https://anshome.org/events-calendar/',
#   'source_name': 'ans'
# }
# is_local = True
# print(handler(event, {}))
