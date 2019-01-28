import ast
import boto3
import bs4
import csv
from datetime import datetime
import requests
import json

bucket = 'aimeeb-datasets-public'
is_local = False
current_date = datetime.today()
url="https://caseytrees.org/events/"+current_date.strftime("%Y-%m")+"/"


def fetch_page(options):
    url = options['url']
    html_doc = requests.get(url).content
    return html_doc


def handle_ans_page(soup):
    events_url = soup.find_all('td')
    websites = []
    #extracts the url for the events
    for row in events_url:
        for column in row.find_all('div'):
            temp = column.text.strip()
            if(temp.isdigit()):
                pass
            else:
                websites.append(column.find('a')['href'])

    #extracts the complete details about events
    events_content = soup.find_all('script',{'type':'application/ld+json'})
    events_complete_data = set()
    for event in events_content:
        for website in websites:
            if(website in event.text.strip()):
                events_complete_data.add(event.text.strip())

    #converts the string to dict
    events_complete_data = ast.literal_eval(list(events_complete_data)[0])

    #extracts the required fields in the output schema
    result_all_event = []
    for con in events_complete_data:
        events_data = {}
        events_data['url'] = con.get('url','no url')
        start = datetime.strptime(con['startDate'][:-6],"%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(con['endDate'][:-6],"%Y-%m-%dT%H:%M:%S")
        events_data['startDate'] = start.strftime('%Y-%m-%d')
        events_data['endDate'] = end.strftime('%Y-%m-%d')
        events_data['startTime'] = start.strftime('%H:%M')
        events_data['endTime'] = end.strftime('%H:%M')
        events_data['address'] = ' '.join(str(x) for x in con['location']['address'].values())
        events_data['latitude'] = con.get('location','no location')
        events_data['venueName'] = con.get('name','no name')
        events_data['latitude'] = "no location"
        events_data['longitude'] = "no location"
        location = con.get('location',False)
        if(location):
            geo = location.get('geo',False)
            if(geo):
                events_data['latitude'] = geo.get('latitude',"no latitude")
                events_data['longitude'] = geo.get('longitude',"no longitude")
            else:
                events_data['latitude'] = "no geo"
                events_data['longitude'] = "no geo"
        result_all_event.append(events_data)
    try:
        #checks if next month calender is present and passes the url to handle_ans_page function
        next = soup.find('li', {'class': 'tribe-events-nav-next'}).a['href']
        page = fetch_page({'url': next})
        soup = bs4.BeautifulSoup(page, 'html.parser')
        result_all_event.extend(handle_ans_page(soup))
    except:
        pass

    return result_all_event


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
event = {
  'url': url,
  'source_name': 'casey_trees'
}
# is_local = False
# print(handler(event, {}))