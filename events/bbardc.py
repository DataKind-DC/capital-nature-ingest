import requests
from bs4 import BeautifulSoup
import json

link = "https://bbardc.org/events/month/"

def export_events(url):

    soup = BeautifulSoup(requests.get(link, timeout=10).content, 'html.parser')
    #soup.prettify()
    
    name_list = soup.find('tbody')
    list_items = name_list.find_all('a', {"class" :"url"})
    
    events = []
    urls = []
    event_errors=[]
    for event in list_items:
        try:
            event_names = event.contents[0]
            links = event.get('href')
            events.append(event_names)
            urls.append(links)
        except IndexError:
            event_errors.append(event)
                
    #Loop through urls and extract information
    
    #Dictionary of all events
    all_events = {}
    
    venues      = []
    address     = []
    start_times = []
    end_times   = []
    dates       = []
    websites    = []
    event_desc  = []
    organizers  = []

    errors = []
    Attribute_errors = []
    Index_errors = []
    
    
    #test_urls =urls[:25]
    
    for links in urls:
        try:
            soup2        = BeautifulSoup(requests.get(links).content, 'html.parser')
            try:
                venue        = soup2.find("dd", {"class":"tribe-venue"}).find("a").text
                get_address  = soup2.find("span",{"class":"tribe-address"})
                show_address = " ".join(str(get_address.text).strip().split('\n') )
            except AttributeError:
                venue        = "No Data"
                get_address  = "No Data"
                show_address = "No Data"  
                Attribute_errors.append(links)
            #Sometimes event has no start time or end time
            try:
                time         = str(soup2.find("div", {"class":"tribe-events-start-time"}).text).strip().split("-")
                start_time   = time[0]
                end_time     = time[1]
            except AttributeError:
                start_time   = "No Time"
                end_time     = "No Time"  
                Attribute_errors.append(links)
            
            #Sometimes the event has no website, if no website then default to https://bbardc.org/
            try:
                website_str      = soup.find('dl').find("a").get('href')
            except AttributeError:
                website_str   = "https://bbardc.org/"
                Attribute_errors.append(links)
            
            #Sometimes the event has no description, default to No Description
            try:
                desc_str      = soup.find("div",class_ ="tribe-events-content").find("p").text
            except AttributeError:
                desc_str   = "No Description"
                Attribute_errors.append(links) 
            
            #Sometimes the event does not have organizer info, default to Event
            try:
                organizer_str      = soup.find("dd", class_="tribe-organizer").find('a').text
            except AttributeError:
                organizer_str   = "No Description"
                Attribute_errors.append(links)   
            except IndexError:
                Index_errors.append(links)   
            
            date = soup2.find('dl').find("dd").find("abbr")["title"]
            venues.append(venue)
            address.append(show_address)
            start_times.append(start_time)
            end_times.append(end_time)
            dates.append(date)
            websites.append(website_str)
            event_desc.append(desc_str)
            organizers.append(organizer_str)
        except Exception as e:
            print(links, " : ", e)
            errors.append(links)
            
    #Append #s to duplicates in "events" list in order to create a dictionary of events
    #Dictionaries cant have duplicates       
                
    from collections import Counter # Counter counts the number of occurrences of each item
    counts = Counter(events) 
    for s,num in counts.items():
        if num > 1: # ignore strings that only appear once
            for suffix in range(1, num + 1): # suffix starts at 1 and increases by 1 each time
                events[events.index(s)] = s +"_"+ str(suffix)
        
    
    
    for i in range(len(events)):
        try:
            all_events[events[i]] = {"Event Cost":"N/A","Event Currency Symbol":"$","Event Description":event_desc[i],"Event End Date":dates[i],
            "Event End Time":end_times[i],"Event Name":events[i],"Event Organizers":organizers[i],"Start Date":dates[i],"Event Start Time":start_times[i],
            "Timezone": "America/New_York","Event Venue Name":venues[i],"Event Website":websites[i],"Address":address[i]
            }
        except Exception as e:
            print(i, "  ",e , all_events)     
        
    final = {}
    final['result'] =all_events 
    all_events_json = json.dumps(final)
    return all_events_json



testing = export_events(link)
print(json.dumps(testing,indent=2))

