import ast
import boto3
import bs4
import csv
from datetime import datetime
import re
import requests
import json
import unicodedata

bucket = 'aimeeb-datasets-public'
is_local = False
url="https://www.sierraclub.org/dc/calendar"


def fetch_page(options):
    url = options['url']
    html_doc = requests.get(url).content
    return html_doc

def handle_ans_page(soup):
    events_url = soup
    return events_url


def handler(event, context):
    url = event['url']
    source_name = event['source_name']
    page = fetch_page({'url': url})
    soup = bs4.BeautifulSoup(page, 'html.parser')
    event_output = handle_ans_page(soup)
    print (event_output)
    # filename = '{0}-results.csv'.format(source_name)
    # if not is_local:
    #     with open('/tmp/{0}'.format(filename), mode = 'w') as f:
    #         writer = csv.DictWriter(f, fieldnames = event_output[0].keys())
    #         writer.writeheader()
    #         [writer.writerow(event) for event in event_output]
    # s3 = boto3.resource('s3')
    # s3.meta.client.upload_file(
    #   '/tmp/{0}'.format(filename),
    #   bucket,
    #   'capital-nature/{0}'.format(filename)
    # )
    # return json.dumps(event_output, indent=2)
    return


# For local testing
event = {
  'url': url,
  'source_name': 'sierra_club_DC'
}
# is_local = False
print(handler(event, {}))

