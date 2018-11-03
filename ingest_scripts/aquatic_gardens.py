import requests
import json
from collections import abc
from dateutil.tz import tzoffset
from datetime import datetime

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



def recursive_items(dictionary):
    '''
    Recursive function to get all key:value pairs in a nested dictionary of unknown depth
    '''
    
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_items(value)
        else:
            yield (key, value)


def filter_data(data):
    '''
    Iterate through all key:value pairs in the data array, returning those that match our schema
    '''
    
    keys = ['longitude', 'latitude', 'dateStart', 'description', 'images', 
            'id', 'dateEnd', 'isRegResRequired', 'infoURL',
            'title','regResInfo']
    key_map = {'title':'name',
               'dateStart':'startDate',
               'dateEnd':'endDate',
               'latitude':'geo.lat',
               'longitude':'geo.lon',
               'infoURL':'url',
               'images':'image',
               'description':'description',
               'isRegResRequired':'registrationRequired',
               'regResInfo':'regResInfo',
               'id':'id'
                }
    filtered_data = []
    for d in data:
        filtered = {k:None for k in key_map.values()}
        for key, _ in recursive_items(d):
            if key in keys:
                mapped_key = key_map[key]
                filtered[mapped_key] = d[key] if mapped_key != 'registrationRequired' else int(d[key])
        filtered_data.append(filtered)
    
    return filtered_data

if __name__ == '__main__':
    data = get_botanical_garden_events('2018-01-01','2018-12-31')
    filtered_data = filter_data(data)
    print(len(filtered_data))
        

    

    
