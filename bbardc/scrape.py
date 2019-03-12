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
    for event in list_items:
        event_names = event.contents[0]
        links = event.get('href')
        events.append(event_names)
        urls.append(links)
    
    
    #Loop through urls and extract information
    
    #Dictionary of all events
    all_events = {}
    
    venues      = []
    address     = []
    start_times = []
    end_times   = []
    dates       = []
    
    errors = []
    Attribute_errors = []
    
    
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
                    
                date = soup2.find('dl').find("dd").find("abbr")["title"]
                venues.append(venue)
                address.append(show_address)
                start_times.append(start_time)
                end_times.append(end_time)
                dates.append(date)
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
        all_events[events[i]] = {"Venue":venues[i],"Address":address[i],"Date":dates[i],"Start_Time":start_times[i],"End_Time":end_times[i]}
        print(i, "  ",all_events)     
        
    import json
    final = {}
    final['result'] =all_events 
    all_events_json = json.dumps(final)
    
    return all_events_json



testing = export_events(link)
print(json.dumps(export_events(link),indent=2))

