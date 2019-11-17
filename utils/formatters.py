from datetime import datetime, timedelta
import re
import string

import geocoder

# defined globally for unicoder function
chars_to_keep = ' '
chars_to_keep += string.punctuation
chars_to_keep += string.ascii_lowercase
chars_to_keep += string.ascii_uppercase
chars_to_keep += string.digits
latinate_chars = 'áéíóúüñ¿¡'
chars_to_keep += latinate_chars
sub_re = re.compile(rf'[^{chars_to_keep}]')

def unicoder(value):
    '''
    Given an object, decode to utf-8 after trying to encode as windows-1252

    Paramters:
        value (obj): could be anything, but should be a string

    Returns:
        If value is a string, return a utf-8 decoded string. Otherwise return value.
    '''
    if not isinstance(value, str):
        return value
    value = re.sub(r' +', ' ', value)
    tokens = value.split()
    v = ''
    for token in tokens:
        if not any(s in token for s in latinate_chars):
            u_token = token.encode('windows-1252', errors='ignore').decode("utf8", errors='ignore')
            v += f'{u_token} '
        else:
            u_token = re.sub(sub_re, '', value)
            v += f'{u_token} '
    v = re.sub(r' +', ' ', v)
    v = v.strip()

    return v


def date_filter(events):
    '''Given an event, determine if it occurs within the next 7 months
    Paramters:
        events (list): a list of dicts, with each dict representing an event

    Returns:
        events_filtered (list): a list of dicts, with each dict representing an event
    '''
    events_filtered = []
    for e in events:
        start_date = e.get('Event Start Date','')
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            continue
        except Exception as e:
            # date musn't follow schema so skip and save logging for the schema test
            continue
        too_far_into_the_future = datetime.now() + timedelta(100)
        date_diff = start - too_far_into_the_future
        if date_diff <= timedelta(210):
            events_filtered.append(e)

    return events_filtered

def tag_events_with_state(events):
    '''
    Tries to prepend event descriptions with the abbreviation of the location's state, e.g. DC, VA, MD

    Parameters:
        events (list): a list of dictionaries, with each dict representing an event

    Returns:
        events_with_states (list): the updated list of dictionaries, with each dict representing an event
    '''
    venue_state_map = {}
    events_with_states = []
    for event in events:
        state_abbreviation = re.compile(r'\b[A-Z]{2}\b')
        event_organizer = event['Event Organizers']
        event_venue = event['Event Venue Name']
        va_orgs = ['Arlington Parks', 'Fairfax Parks']
        dc_orgs = ['National Park Service, Rock Creek Park', 'United States Botanic Garden']
        md_orgs = ['Montgomery Parks']
        if event_organizer in va_orgs or 'virginia' in event_venue.lower():
            event_state = '(VA)'
        elif event_organizer in dc_orgs:
            event_state = '(DC)'
        elif event_organizer in md_orgs or 'maryland' in event_venue.lower():
            event_state = '(MD)'
        else:
            event_state = None
        if not event_state:
            try:
                first_char_is_digit = event_venue[0].isdigit()
            except IndexError:
                #must be no event venue, so skip it and save logging for the schema test
                continue
            if first_char_is_digit:
                m = state_abbreviation.findall(event_venue)
                if 'DC' in m:
                    event_state = '(DC)'
                elif 'VA' in m:
                    event_state = '(VA)'
                elif 'MD' in m:
                    event_state = '(MD)'
                if not event_state:
                    if event_venue in venue_state_map:
                        event_state = venue_state_map[event_venue]
                    else:
                        #split at comma in case there are multiple locations
                        venue = event_venue.split(",")[0]
                        g = geocoder.osm(venue)
                        try:
                            event_state = g.json['raw']['address']['state']
                            event_state = f'({event_state})'
                            venue_state_map[event_venue] = event_state
                        except TypeError:
                            pass
        event_description = event['Event Description']
        if event_state:
            updated_event_description = f'{event_state} {event_description}'
            event['Event Description'] = updated_event_description
        events_with_states.append(event)

    return events_with_states