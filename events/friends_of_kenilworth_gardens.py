from bs4 import BeautifulSoup
import requests
import json
import bs4
import sys
from datetime import datetime


def soupify_event_page(url='http://www.friendsofkenilworthgardens.org/news-and-events/events/2019/03/'):
    # Extract the event url from the website calendar

    try:
        r = requests.get(url)
    except:
        return
    content = r.content
    soup = bs4.BeautifulSoup(content, 'html.parser')
    # Extract the event's eventbrite url
    events_url = soup.find_all('div', {'class': 'events-container list-view'})
    for j_event_url in events_url:
        m_event_url = j_event_url.h3.a['href']
        # Cleaning url link to get event's eventbrite url
        event_url = m_event_url.split('2019/01/09/')[1]

        # Go to Eventbrite event's page
        r = requests.get(event_url)
        content = r.content
        soup = BeautifulSoup(content, 'html.parser')

    return soup


def schematize_event_date(event_date):
    '''
    Converts a date like '2019-05-25T09:00:00-0400' to '2019-05-25'
    '''
    schematize_event_date = event_date[0:10]
    return schematize_event_date


def schematize_event_time(event_time):
    '''
    Converts a time string like '2019-04-13T12:00:00-0400' to '12:00:00'
    '''
    schematize_event_time = event_time[11:19]
    return schematize_event_time


# Given a beautiful soup object, return a list of events on that page
def main():
      soup = soupify_event_page()

      if not soup:
          sys.exit(1)


      #Extract events details
      events_details = soup.findAll('script',{'type':'application/ld+json'})

      # Gather all the required fields into output schema
      event_output = []
      for event_details in eval(events_details[1].text.strip()):
          # Get end date and times of the event and return only current or future events
          eventEnd = datetime.strptime(event_details['endDate'][:-6], "%Y-%m-%dT%H:%M:%S")

      # Return only unexpired events
          if eventEnd > datetime.now():

              event_data = {
                'Event Name': event_details['name'],
                'Event Description': event_details['description'],
                'Event Start Date': schematize_event_date(event_details['startDate']),
                'Event Start Time': schematize_event_time(event_details['startDate']),
                'Event End Date': schematize_event_date(event_details['endDate']),
                'Event End Time': schematize_event_time(event_details['endDate']),
                'Event Time Zone': "America/New_York",
                'Event Venue Name': event_details['location']["name"],
                'Event Organizer': event_details['organizer']["name"],
                'Event Price': event_details['offers']['lowPrice'],
                'Event Currency Symbol': event_details['offers']['priceCurrency'],
                'Event Currency Position': "prefix",
                'Event Website': event_details['url'],
                'Event Featured Image': event_details['image'],
                'All Day Event': False,
                # commenting addresss, latitude and longitude fields for now as The WordPress Event plugin doesn't
                # expect these fields, but we might eventually use their Map plugin, which would need those geo fields
                #'Event Latitude': event_details['location']['geo']['latitude'],
                #'Event Longitude': event_details['location']['geo']['longitude'],
                #'Event Address': event_details['location']['address']['streetAddress']+', '+
                #                 event_details['location']['address']['addressLocality']+" "+
                #                 event_details['location']['address']['addressRegion']
              }
              event_output.append(event_data)
      print(event_output)
      return event_output



if __name__ == '__main__':
    events = main()
