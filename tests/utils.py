import re
import requests

url_regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class EventDateFormatError(Exception):
   """The Event Start Data and Event End Date fields must be strings following
   the "%Y-%m-%d" format. Examples:  '1966-01-01' or '1965-12-31'
   """
   pass   

class EventTimeFormatError(Exception):
   """The Event Start Time and Event End Time fields must be strings following
   the "%H:%M:%S" format. Examples: '21:30:00' or '00:50:00'
   """
   pass

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


def exceptionCallback(request, uri, headers):
    '''
    Create a callback body that raises an exception when opened. This simulates a bad request.
    '''
    raise requests.ConnectionError('Raising a connection error for the test. You can ignore this!')