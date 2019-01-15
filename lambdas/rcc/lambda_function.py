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
    events = soup.find_all('a', {'class': 'timely-event'})
    event_output = []
    for e in events:
        event_data = {
            'Event Name': e.find('div', {'class': 'timely-title'}).find('span').text,
            'Event Organizer Name(s) or ID(s)': 'Rock Creek Conservancy',
            'Event Venue Name': e.find('span', {'class': 'timely-venue'}).text.strip()[2:],
            'Event Website': e.attrs['href'],
            'Event Start Date': e.attrs['data-date'],
            'Event Start Time': e.find('div', {'class': 'timely-start-time'}).text.strip(),
            # 'Event End Date': None,
            # 'Event End Time': None,
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
    else:
        with open('{0}'.format(filename), mode = 'w') as f:
            writer = csv.DictWriter(f, fieldnames = event_output[0].keys())
            writer.writeheader()
            [writer.writerow(event) for event in event_output]
    return json.dumps(event_output, indent=2)

# For local testing
if __name__ == "__main__":
    event = {
        'url': 'https://events.time.ly/8ib56fp',
        'source_name': 'rcc'
    }
    is_local = True
    print(handler(event, {}))
