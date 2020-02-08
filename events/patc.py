import logging
import posixpath
import requests

from bs4 import BeautifulSoup
import more_itertools
import pandas as pd

URL_BASE = 'https://www.patc.net/PATC/Calendar/PATC/'
CALENDAR_BASE_URL = 'Custom/Calendar.aspx?hkey=9fc06544-1c54-4a47-9efc-8fcd2420a646'
KEYWORDS = [
    'Start Time', 'Start Date', 'Contact', 'Email', 'Event Category']


def make_request_content(url_subpath):
    parse_link = posixpath.join(URL_BASE, url_subpath)
    res = requests.get(parse_link)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, features='lxml')
    return soup


def find_event_data(link):
    res = make_request_content(link)

    # there appears to be faulty calendar events that are unable to be parsed
    try:
        results = {
            'Event Name': res.findAll('th')[-1].getText().strip(),
            'Event Venue Name': res.findAll('th')[-1].getText().strip(),
            'Description': res.findAll('p')[-1].getText().strip()
        }
    except IndexError:
        return

    for para in res.findAll('p'):
        if any([word + ':' in para.getText() for word in KEYWORDS]):
            logging.info('found event info: %s', para.getText().strip())
            header = more_itertools.one(para.findAll('strong'))
            category, _, _ = header.getText().rpartition(':')
            value = more_itertools.last(para.children)

            # sometimes BS4 will return NavigableString or some subclass
            # that appears to be string, we need to encode them to remove
            # non-ascii characters and then decode them from binary
            if not isinstance(value, str):
                value = value.getText()
            results[category] = value.encode('ascii', 'ignore').decode().strip()
    return results


def scrape_for_events():
    records = []
    events = make_request_content(CALENDAR_BASE_URL)

    for event in events.findAll('a'):
            # impute empty string because you cannot do an equality check on NoneType
        event_link = event.attrs.get('href', '')
        if 'calendar.aspx' in event_link:
            url = posixpath.split(event_link)[-1]
            logging.info('found calendar event, %s', url)
            data = find_event_data(posixpath.join('Custom', url))

            # there appears to be faulty calendar events that are unable to be parsed
            if data:
                records.append(data)

    data = pd.DataFrame.from_records(records)
    data['Start Date'] = data['Start Date'].astype('datetime64[ns]')
    data['End Date'] = data['Start Date'] # these are not end dates
    data['All Day Event'] = False
    data['Timezone'] = 'America/New_York' # this is assumed to be EST
    data['End Time'] = '23:59:59' # there are no end times, assuming to be the end of the day
    data['Event Organizers'] = data['Contact']

    return data


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    try:
        events = scrape_for_events()
    except:
        import ipdb; ipdb.post_mortem()
