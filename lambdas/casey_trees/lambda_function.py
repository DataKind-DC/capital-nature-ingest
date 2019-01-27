import requests
from bs4 import BeautifulSoup
import ast
from datetime import datetime
import pprint


bucket = 'aimeeb-datasets-public'
is_local = False
current_date = datetime.today()
url="https://caseytrees.org/events/"+current_date.strftime("%Y-%m")+"/"

def extract_data(url):
    html_doc = requests.get(url).content
    return html_doc


def extract_events(url):
    page = extract_data(url)
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
        ind_event['url'] = con.get('url','no url')
        start = datetime.strptime(con['startDate'][:-6],"%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(con['endDate'][:-6],"%Y-%m-%dT%H:%M:%S")
        ind_event['startDate'] = start.strftime('%Y-%m-%d')
        ind_event['endDate'] = end.strftime('%Y-%m-%d')
        ind_event['startTime'] = start.strftime('%H:%M')
        ind_event['endTime'] = end.strftime('%H:%M')
        ind_event['address'] = ' '.join(str(x) for x in con['location']['address'].values())
        ind_event['latitude'] = con.get('location','no location')
        ind_event['venueName'] = con.get('name','no name')
        ind_event['latitude'] = "no location"
        ind_event['longitude'] = "no location"
        location = con.get('location',False)
        if(location):
            geo = location.get('geo',False)
            if(geo):
                ind_event['latitude'] = location.get('latitude',"no latitude")
                ind_event['longitude'] = location.get('longitude',"no longitude")
            else:
                ind_event['latitude'] = "no geo"
                ind_event['longitude'] = "no geo"
        result_all_event.append(ind_event)
    try:
        next = soup.find('li', {'class': 'tribe-events-nav-next'}).a['href']
        result_all_event.extend(extract_events(next))
    except:
        pass

    return result_all_event


pprint.pprint(extract_events(url))