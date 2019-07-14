from datetime import datetime
import re

import requests

url_regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
 

def is_phonenumber_valid(phone_number):
    '''
    Tests if a phone number is formatted as "+1-326-437-9663"
    
    Parameters:
        phone_number (str):

    Returns:
        True is the number is properly formatted; False otherwise
    '''
    starts_with_plus = phone_number.startswith("+")
    contains_three_dashes = phone_number.count("-")
    all_digits = phone_number.replace("-",'').isdigit()
    result = starts_with_plus and contains_three_dashes and all_digits
    
    return result


def schema_test_required(events):
    '''Test if the required fields are present for each event.'''
    if not events:
        # If there weren't any events, return True
        return True
    keys = set().union(*(d.keys() for d in events))
    schema = {'Event Name', 'Event Description', 'Event Start Date',
              'Event Start Time', 'Event End Date', 'Event End Time',
              'Timezone', 'All Day Event', 'Event Venue Name',
              'Event Organizers', 'Event Cost', 'Event Currency Symbol',
              'Event Category', 'Event Website'}
    result = schema.issubset(keys)
    if not result:
        missing_fields = schema - keys
        for f in missing_fields:
            print(f"Event schema is missing a required field:  {f}\n")
        result = False
    return result


def schema_test_all(events):
    '''Tests if all of the event fields conform in name to the schema.'''

    if not events:
        # If there weren't any events, return True
        return True
    keys = set().union(*(d.keys() for d in events))
    schema = {'Do Not Import','Event Name','Event Description','Event Excerpt',
              'Event Start Date','Event Start Time','Event End Date','Event End Time',
              'Timezone','All Day Event','Hide Event From Event Listings',
              'Event Sticky in Month View','Feature Event','Event Venue Name',
              'Event Organizers','Event Show Map Link',
              'Event Show Map','Event Cost','Event Currency Symbol',
              'Event Currency Position','Event Category','Event Tags',
              'Event Website','Event Featured Image','Allow Comments',
              'Event Allow Trackbacks and Pingbacks'}
    result = keys.issubset(schema)
    if not result:
        extra_fields = keys - schema
        for f in extra_fields:
            print(f"Event schema contains a superfluous field:  {f}\n")

    return result


def schema_test_types(events):
    '''Test each field's data types'''
    if not events:
        # If there weren't any events, return True
        return True
    
    booleans = {'All Day Event','Hide from Event Listings','Sticky in Month View',
                'Event Show Map Link','Event Show Map','Allow Comments',
                'Allow Trackbacks and Pingbacks'}
    comma_delimited = {'Event Venue Name','Event Organizers','Event Category','Event Tags'}
    string = {'Event Description','Event Excerpt','Event Name'}
    date = {'Event Start Date', 'Event End Date'}
    time = {'Event Start Time','Event End Time'}
    url = {'Event Website', 'Event Featured Image'}
    for event in events:
        for k in event:
            # boolean fields
            if k in booleans:
                val = event[k]
                is_bool = isinstance(val, bool) or val in ['False', 'True']
                if not is_bool:
                    msg = f"Non boolean value of {val} found in {k} event field of {event}"
                    raise Exception (msg)
            # Tests if the str and comma delim event field types are strings
            elif k in string or k in comma_delimited:
                val = event[k]
                is_str = isinstance(val, str)
                if not is_str:
                    msg = f"Non string value of {val} found in {k} event field of {event}"
                    raise Exception (msg)
            # Tests if the currency symbol is a dollar sign
            elif k == 'Event Currency Symbol':
                val = event[k]
                is_dollar_sign = val == "$"
                if not is_dollar_sign:
                    msg = f"Non '$' value of {val} found in {k} event field of {event}"
                    raise Exception (msg)
             # Tests if the event cost is a string of digits
            elif k == 'Event Cost':
                val = event[k]
                val = val.lower().replace(",",'').replace(".",'').replace("free",'')
                #empty strings are "falsy"
                is_digit = val.isdigit() or not val
                if not is_digit:
                    msg = f"Invalid value of {val} found in {k} event field of {event}."
                    raise Exception (msg)
            # Tests if the timezone event field is 'America/New_York'
            elif k == 'Timezone':
                val = event[k]
                is_tz = val == 'America/New_York'
                if not is_tz:
                    msg = f"Non '$' value of {val} found in {k} event field of {event}"
                    raise Exception (msg)
            # Tests if the event start/end date fields are "%Y-%m-%d" 
            # Examples: '1966-01-01' or '1965-12-31'
            elif k in date:
                val = event[k]
                try:
                    _dt_val = datetime.strptime(val, "%Y-%m-%d")
                except Exception as e:
                    # ValueError raised by datetime.strptime when invalid value encountered
                    msg = f"{e}: Incorrect date format of {val} found in {k} event field of {event}"
                    raise Exception (msg)
            # Tests if the Event Start Time and Event End Time fields follow
            # the "%H:%M:%S" format. Examples: '21:30:00' or '00:50:00'
            elif k in time:
                val = event[k]
                if val != '':
                    try:
                        _dt_val = datetime.strptime(val, "%H:%M:%S")
                    except Exception as e:
                        if event.get('All Day Event'):
                            # All day events can have missing values
                            continue
                        msg = f"{e}: Incorrect time format of {val} found in {k} event field of {event}"
                        raise Exception (msg)
            # Tests if the event website and event featured image fields contain strings
            # that pass Django's test as urls
            elif k in url:
                val = event[k]
                if not val:
                    continue
                m = re.match(url_regex, val)
                if not m:
                    msg = f"Invalid url of {val} found in {k} event field of {event}"
                    raise Exception (msg)
            # Tests if the Event Currency Position is 'prefix', 'suffix', or ''
            elif k == 'Event Currency Position':
                val = event[k]
                expected_vals = {'prefix', 'suffix', ''}
                result = val in expected_vals
                if not result:
                    msg = (
                           f"Invalid value of {val} found in {k} event field of {event}\n"
                           "Value must be one of 'prefix', 'suffix' or ''"
                    )
                    raise Exception (msg)
            # Tests if the phone number string is formatted like:  "+1-326-437-9663"
            elif k == 'Event Phone':
                val = event[k]
                result = is_phonenumber_valid(val)
                if not result:
                    msg = f"Invalid phone number of {val} found in {k} event field of {event}"
                    raise Exception (msg)
            else:
                raise Exception (f"Encountered an event field ({k}) that's not in our schema.")

    # Return True if we made it to the end without raising an Exception
    return True