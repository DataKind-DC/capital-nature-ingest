import  requests
from bs4 import BeautifulSoup
import ast
from datetime import datetime
import pprint


bucket = 'aimeeb-datasets-public'
is_local = False

def extract_data():
    url = "https://caseytrees.org/events/2019-01/"
    html_doc = requests.get(url).content
    return html_doc


def extract_events():
    page = extract_data()
    soup = BeautifulSoup(page, "html.parser")
    events_url = soup.find_all('td')
    websites = []
    for row in events_url:
        for column in row.find_all('div'):
            temp = column.text.strip()
            if(temp.isdigit()):
                pass
            else:
                websites.append(column.find('a')['href'])

    events_content = soup.find_all('script',{'type':'application/ld+json'})
    final_content = set()
    for event in events_content:
        for website in websites:
            if(website in event.text.strip()):
                final_content.add(event.text.strip())

    final_content = ast.literal_eval(list(final_content)[0])

    #extracts the required fields in the output schema
    result_all_event = []
    for con in final_content:
        ind_event = {}
        ind_event['url'] = con['url']
        start = datetime.strptime(con['startDate'][:-6],"%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(con['endDate'][:-6],"%Y-%m-%dT%H:%M:%S")
        ind_event['startDate'] = start.strftime('%Y-%m-%d')
        ind_event['endDate'] = end.strftime('%Y-%m-%d')
        ind_event['startTime'] = start.strftime('%H:%M')
        ind_event['endTime'] = end.strftime('%H:%M')
        ind_event['address'] = ' '.join(str(x) for x in con['location']['address'].values())
        ind_event['latitude'] = con['location']['geo']['latitude']
        ind_event['venueName'] = con['name']
        ind_event['longitude'] = con['location']['geo']['longitude']
        result_all_event.append(ind_event)

    return result_all_event


pprint.pprint(extract_events())