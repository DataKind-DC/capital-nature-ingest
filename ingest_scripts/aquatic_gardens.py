import requests
import json

def get_botanical_garden_events(start_date, end_date):
    '''
    Get events data from the National Park Aquatic Gardens EventCalendarService API
    
    Parameters:
        start_date (str): a date string of the form YYYY-MM-DD. Events will be inclusive of this start date.
        end_data (str): a date string of the form YYYY-MM-DD. Events will be inclusive of this end date.
        
    Returns:
        data (list): a list of dicts representing each event. Could convert dicts to json.
    '''
    url = f'https://www.nps.gov/common/components/nps/eventcalendar/EventCalendarService.cfc'+\
          f'?method=getEvents&parkCode=keaq&dateStart={start_date}&dateEnd={end_date}'+\
          f'&expandRecurring=true'
    r = requests.get(url)
    r_json = r.json()
    data = r_json['data']
    
    return data

data = get_botanical_garden_events('2018-01-01','2018-12-31')

if __name__ == '__main__':
    data = get_botanical_garden_events('2018-01-01','2018-12-31')
