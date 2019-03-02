
# ![image.png](attachment:image.png)
# 
# 
# 
# ### Events Scraping for The Nature Conservancy (TNC) - Virginia 
# 
# Global Site: https://www.nature.org/en-us/


import bs4
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def main():
    
    url = 'https://uv6jfqw6q8.execute-api.us-east-1.amazonaws.com/prod/search?q=*&q.parser=lucene&fq=(and%20template_name:%27eventdetailpage%27search_by_domain:%27nature_usa_en%27(or%20geographic_location:%27all_locations%27(and%20event_region_title:%27United%20States%27event_locale_title:%27Virginia%27))event_start_date:%20%5B%272019-02-19T00:00:00Z%27,%7D)&sort=event_start_date_sort%20asc&size=200'
    html_doc = requests.get(url).content

    page = requests.get(url)
    soup = bs4.BeautifulSoup(page.content, 'html.parser')

    soup=str(soup)
    events=json.loads(soup)

    events.keys()
    hits=events['hits']

    hits.keys()
    hit=hits['hit']

    
    events_dict = []

    for i in range(len(hit)):
        event=hit[i]
        fields=event['fields']
       
        start_date_s = fields['event_dates'][:6]+", "+fields['event_dates'][-4:]
        
        start_date=datetime.strptime(start_date_s,'%b %d, %Y').strftime('%Y-%m-%d')             

        if len(fields['event_dates'])>15:

            end_date_s = fields['event_dates'][-12:]  

        else:
            end_date_s = start_date_s

        end_date=datetime.strptime(end_date_s,'%b %d, %Y').strftime('%Y-%m-%d')   # format of conditional statements 

        time=fields['event_timings']

        start_time_1 = datetime.strptime(time[:8],'%I:%M %p').time() #use I for converting AM/PM to 24 hour
        end_time_1 =datetime.strptime(time[-8:],'%I:%M %p').time()

        diff = end_time_1.hour - start_time_1.hour #use .hour to enable datetime.time operations

        if diff >= 7:
            all_day = True
        all_day = False

        start_time=start_time_1.strftime('%H:%M:%S')
        end_time=end_time_1.strftime('%H:%M:%S')
        
        event_website='https://www.nature.org'+fields['link']

        #scrape event venue from event website
        url2=event_website
        html_doc = requests.get(url2).content
        soup = bs4.BeautifulSoup(html_doc, 'html.parser')
        
        venue=soup.find_all('p',{'class': 'txt-clr-g1'})[-1:]
        event_venue=', '.join(venue[0].get_text(strip=True).split('\r\n'))
        
        event_description=str.strip(fields['description'])
        
        event_name=fields['title']
       
        event_categories=", ".join(fields['topic_title'])


        dict = {'Event Start Date': start_date,
              'Event End Date': end_date,
              'Event Start Time': start_time,
              'Event End Time': end_time,
              'Event Website': event_website,
              'Event Name': event_name,
              'Event Description':event_description,
              'Event Venue Name': event_venue,
              'All Day Event': all_day,
              'Event Category':event_categories,
              'Event Cost':'',
              'Event Currency Symbol':'$',
              'Timezone':'America/New_York',
              'Event Organizers': 'The Nature Conservancy (Virginia)'}

        event_dict=events_dict.append(dict)

    return events_dict

if __name__ == '__main__':
    events_dict = main()

main()

