import ast
import bs4
from datetime import datetime
import re
import requests
import unicodedata


def fetch_page_soup(url):
    r = requests.get(url)
    content = r.content
    soup = bs4.BeautifulSoup(content, 'html.parser')
    return soup

def parse_event_cost(event_cost):
    if event_cost == "Donation":
        event_cost = event_cost.replace("Donation","0")
        return event_cost
    else:
        currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
        event_cost = re.findall(currency_re, event_cost)
        if len(event_cost) > 0:
            event_cost = event_cost[0].split(".")[0].replace("$",'')
            event_cost = ''.join(s for s in event_cost if s.isdigit())
            return event_cost
        else:
            return ''

def handle_ans_page(soup):
    events_url = soup.find_all('td')
    websites = []
    categoryclasses = {}
    #extracts the url for the events
    for row in events_url:
        for column in row.find_all('div'):
            temp = column.text.strip()
            if(temp.isdigit()):
                pass
            else:
                websites.append(column.find('a')['href'])
                # not sure if this is a good way. to get the exact tags we might have to call the url and get the values
                # under event tag
                category_classes_dict = ast.literal_eval(column['data-tribejson'])\
                                                            ['categoryClasses'].split(" ")
                event_category_classes=""
                for each_categoryclasses in category_classes_dict:
                    if("tribe-events-category-" in each_categoryclasses):
                        if(event_category_classes != ""):
                            event_category_classes += ","
                        event_category_classes += each_categoryclasses.replace("tribe-events-category-","")
                categoryclasses[column.find('a')['href']] = event_category_classes

    #extracts the complete details about events
    events_content = soup.find_all('script',{'type':'application/ld+json'})
    events_complete_data = set()
    for event in events_content:
        for website in websites:
            if(website in event.text.strip()):
                events_complete_data.add(event.text.strip())

    #converts the string to dict
    try:
        events_complete_data = ast.literal_eval(list(events_complete_data)[0])
    except:
        return []

    #extracts the required fields in the output schema
    result_all_event = []
    for con in events_complete_data:
        events_data = {}
        # some html string is present in event name default adding this to format it
        events_name_data = bs4.BeautifulSoup(con.get('name',''), 'html.parser')
        events_data['Event Name'] = events_name_data.get_text()
        events_data['Event Website'] = con.get('url','')
        events_data['Event Category'] = categoryclasses.get(events_data['Event Website'],'')
        start = datetime.strptime(con['startDate'][:-6],"%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(con['endDate'][:-6],"%Y-%m-%dT%H:%M:%S")
        events_data['Event Start Date'] = start.strftime('%Y-%m-%d')
        events_data['Event End Date'] = end.strftime('%Y-%m-%d')
        events_data['Event Start Time'] = start.strftime('%H:%M:%S')
        events_data['Event End Time'] = end.strftime('%H:%M:%S')
        events_data['Timezone'] = "America/New_York"
        events_data['Event Venue Name'] = con['location']['name']
        events_data['Event Featured Image'] = con.get('image','')
        events_data['Event Description'] = unicodedata.normalize('NFKD', get_event_description(events_data['Event Website']))
        events_data['Event Cost'] = parse_event_cost(con['offers']['price'])
        events_data['Event Currency Symbol'] = "$"
        events_data['All Day Event'] = False
        organizer = con.get('organizer', False)
        if(organizer):
            events_data['Event Organizers'] = organizer.get('name',"")
        else:
            events_data['Event Organizers'] = ""
        # commenting addresss, latitude and longitude fields for now as The WordPress Event plugin doesn't
        # expect these fields, but we might eventually use their Map plugin, which would need those geo fields 
        # events_data['address'] = ' '.join(str(x) for x in con['location']['address'].values())
        # commenting the latitude and longtide fields
        # events_data['latitude'] = "no location"
        # events_data['longitude'] = "no location"
        # location = con.get('location', False)
        # if(location):
        #     geo = location.get('geo', False)
        #     if(geo):
        #         events_data['latitude'] = geo.get('latitude',"no latitude")
        #         events_data['longitude'] = geo.get('longitude',"no longitude")
        #     else:
        #         events_data['latitude'] = "no geo"
        #         events_data['longitude'] = "no geo"
        result_all_event.append(events_data)
    try:
        #checks if next month calender is present and passes the url to handle_ans_page function
        next_url = soup.find('li', {'class': 'tribe-events-nav-next'}).a['href']
        soup = fetch_page_soup(next_url)
        result_all_event.extend(handle_ans_page(soup))
    except:
        pass

    return result_all_event



def get_event_description(url):
    soup = fetch_page_soup(url)
    events_url = soup.find('meta', {'property': 'og:description'})['content']
    
    return events_url

def main():
    current_date = datetime.today()
    url="https://caseytrees.org/events/"+current_date.strftime("%Y-%m")+"/"
    soup = fetch_page_soup(url)
    events = handle_ans_page(soup)
    
    return events

if __name__ == '__main__':
    events = main()
    

