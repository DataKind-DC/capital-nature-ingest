from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime


def get_event_cost(soup):
    currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
    b_tags = soup.find_all('b')
    for b in b_tags:
        if 'Cost' in b.text:
            event_cost = b.nextSibling.strip()
            event_cost = re.findall(currency_re, event_cost)
            if len(event_cost) > 0:
                event_cost = event_cost[0].split(".")[0].replace("$",'')
                event_cost = ''.join(s for s in event_cost if s.isdigit())
                return event_cost
    return ''


def get_event_date_from_event_website(event_website):
    url_tail = event_website.split('/')[-1]
    if all(s.isdigit() for s in url_tail):
        event_date = '/'.join([url_tail[i:i+2] for i in range(0, len(url_tail), 2)])
        event_date_year = f'20{event_date[-2:]}'
        event_date = event_date[:-2] + event_date_year
        event_date = schematize_event_date(event_date)
        return event_date
    else:
        return


def get_event_start_date(soup, event_website):
    start_date = get_event_date_from_event_website(event_website)
    if start_date:
        return start_date
    else:
        h5_divs = soup.find_all('h5')
        try:
            start_date = h5_divs[-1].text.split()[0]
        except IndexError:
            start_date = ''
    split_date = start_date.split("/")
    if len(start_date) > 0:
        if len(split_date[0]) == 1:
            split_date[0] = f'0{split_date[0]}'
        start_date = "/".join(split_date)
    start_date = schematize_event_date(start_date)
    return start_date


def get_start_times(soup):
    calendar_descriptions = soup.find_all('div',{'calendar-description'})
    start_times = []
    for calendar_description in calendar_descriptions:
        start_time = calendar_description.get_text().strip().split(",")[0]
        start_times.append(start_time)
    start_times = [schematize_event_time(x) for x in start_times]
    return start_times


def get_event_description(soup):
    p_texts = []
    for p in soup.find_all("p"):
        p_text = p.get_text()
        p_texts.append(p_text)
    sorted_descriptions = sorted(p_texts, key = len)
    longest_description = sorted_descriptions[-1].strip()
    if longest_description.startswith('Click to view in Google Maps'):
        event_description = sorted_descriptions[-3].strip()
    else:
        event_description = longest_description
    event_description = event_description
    if event_description.startswith('Please wait while we redirect'):
        return
    else:
        if event_description.startswith("Event Description\n"):
            event_description = event_description.replace("Event Description\n",'', 1)
        if event_description.startswith("("):
            between_parentheses = event_description[event_description.find("(")+1:event_description.find(")")]
            to_replace = f'({between_parentheses})'
            event_description = event_description.replace(to_replace,'').strip()
        if "Golf Course" in event_description:
            golf_index = event_description.find("Golf Course")
            event_description = event_description[golf_index+13:]
        return event_description


def get_event_venue(soup):
    try:
        event_venue = soup.find('h3').find('span').get_text().replace(' Location','')
    except AttributeError:
        p_tags = soup.find_all('p')
        p_tag_index = 0
        highest_br_count = 0
        for i, p in enumerate(p_tags):
            try:
                br_count = len(p.findChildren('br'))
            except TypeError:
                continue
            if br_count > highest_br_count:
                p_tag_index = i
            highest_br_count = br_count
        event_venue = p_tags[p_tag_index]
        test = [x.strip() for x in event_venue.get_text().split("\n")]
        event_venue = next(x for x in test if len(x)>0)

    return event_venue

def parse_event_website(event_website):
    try:
        r = requests.get(event_website)
    except:
        event_cost = None
        event_description = None
        event_venue = None
        start_date = None
        return event_cost, event_description, event_venue, start_date
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    page_title_lowered = soup.find('div', {'class':'page-title'}).text.strip().lower()
    if 'canceled' in page_title_lowered:
        event_cost = None
        event_description = None
        event_venue = None
        start_date = None
    else:
        event_cost = get_event_cost(soup)
        event_description = get_event_description(soup)
        event_venue = get_event_venue(soup)
        start_date = get_event_start_date(soup, event_website)

    return event_cost, event_description, event_venue, start_date

def schematize_event_date(event_date):
    '''
    Converts a date string like '01/27/2019' to '2019-01-27'
    '''
    try:
        datetime_obj = datetime.strptime(event_date, "%m/%d/%Y")
        schematized_event_date = datetime.strftime(datetime_obj, "%Y-%m-%d")
    except ValueError:
        #format might be like 012619
        try:
            datetime_obj = datetime.strptime(event_date, "%m%d%y")
            schematized_event_date = datetime.strftime(datetime_obj, "%Y-%m-%d")
        except ValueError:
            schematized_event_date = ''
    
    return schematized_event_date


def schematize_event_time(event_time):
    '''
    Converts a time string like '1:30PM' to 24hr time like '13:30:00'
    '''
    try:
        datetime_obj = datetime.strptime(event_time, "%I:%M%p")
        schematized_event_time = datetime.strftime(datetime_obj, "%H:%M:%S")
    except ValueError:
        schematized_event_time = ''
    
    return schematized_event_time


def main():
    r = requests.get('https://www.fairfaxcounty.gov/parks/park-events-calendar')
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    start_times = get_start_times(soup)
    title_divs = soup.find_all('div', {'class':'calendar-title'})
    domain = 'https://www.fairfaxcounty.gov'
    events = []
    for i, title_div in enumerate(title_divs):
        event_name = title_div.text.strip()
        try:
            event_website = title_div.find('a', href=True)['href']
        except KeyError:
            #if there's no event website, skip since we won't get needed info without it
            continue
        if not domain in event_website:
            event_website = domain + event_website
        start_time = start_times[i]
        event_cost, event_description, event_venue, start_date = parse_event_website(event_website)
        if event_cost and event_description:
            event = {'Event Start Date': start_date,
                     'Event End Date': start_date, #same as start date
                     'Event Start Time': start_time,
                     'Event End Time':'',#there are never any end times
                     'Event Website': event_website,
                     'Event Name': event_name,
                     'Event Venue Name': event_venue,
                     'Event Cost': event_cost,
                     'Event Description': event_description,
                     'Event Currency Symbol':'$',
                     'Timezone':'America/New_York',
                     'Event Organizers':'Fairfax Parks',
                     'Event Category':'',
                     'All Day Event':False} #doesn't seem like any events are all day
            events.append(event)

    return events

if __name__ == '__main__':
    events = main()