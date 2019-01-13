import bs4
import requests
import json
import csv
import boto3
import dateparser
import re

bucket = 'aimeeb-datasets-public'
is_local = False

def fetch_page(options):
  url = options['url']
  html_doc = requests.get(url).content
  return html_doc

# Given a beautiful soup object, return a list of events on that page
def handle_brookside_gardens_page(soup):
  pattern = re.compile('.*to ')
  event_url_root = 'https://www.montgomeryparks.org'
  event_block = soup.find_all('div', {'class': 'event-item'})
  event_list = event_block[0].find('ul')
  events = event_list.find_all('li')
  event_output = []
  i = 1

  for e in events:
    # date/time is within <span class="time"> and is formatted like this: Mon. January 14th, 2019 10:30am to  12:00pm
    spanTime = e.find('span', {'class': 'time'}).text.strip()
    print(spanTime)
    match = pattern.match(spanTime)
    event_datetime = dateparser.parse(match.group()[0:-4])
    event_date = event_datetime.strftime('%m/%d/%Y')
    event_starttime = event_datetime.strftime('%I:%M%p')
    event_endtime = spanTime[-7:].upper()

    event_data = {
      'Event Venue Name': 'Brookside Gardens',
      'Event Name': e.find('span', {'class': 'event-name'}).text.encode('utf-8'),
      'Event Venue Address': '1800 Glenallan Avenue Wheaton, MD 20902',
      'latitude': 39.059830,
      'longitude': -77.033090,
      'Event Website': event_url_root + e.find('a')['href'],
      'Event Start Date': event_date,
      'Event Start Time': event_starttime,
      'Event End Date': event_date,
      'Event End Time': event_endtime
    }
    event_output.append(event_data)
    print(i)
    i += 1
  return event_output

def handler(event, context):
  url = event['url']
  source_name = event['source_name']
  page = fetch_page({'url': url})
  soup = bs4.BeautifulSoup(page, 'html.parser')
  event_output = handle_brookside_gardens_page(soup)
  filename = '{0}-results.csv'.format(source_name)
  output_file = filename if is_local else '/tmp/{0}'.format(filename)

  with open(output_file, mode = 'w') as f:
    writer = csv.DictWriter(f, fieldnames = event_output[0].keys())
    writer.writeheader()
    [writer.writerow(event) for event in event_output]

  if not is_local:
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(
      output_file,
      bucket,
      'capital-nature/{0}'.format(filename)
    )
  return json.dumps(event_output, indent=2)

# For local testing
# event = {
#   'url': 'https://www.montgomeryparks.org/calendar/?park=brookside%20gardens',
#   'source_name': 'brookside-gardens'
# }
# is_local = True
# events_dict = handler(event, {})
# print(events_dict)
