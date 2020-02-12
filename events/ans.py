from datetime import datetime, timedelta
import json
import logging
import re

import bs4
import requests

logger = logging.getLogger(__name__)


def soupify_page(url='https://anshome.org/events-calendar/'):
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(f'Exception making GET to {url}: {e}', exc_info=True)
        return
    content = r.content
    soup = bs4.BeautifulSoup(content, 'html.parser')

    return soup


def get_event_data(soup):
    scripts = soup.find_all('script', {'type': 'application/ld+json'})
    comma_hugged_by_quotes = re.compile(r'(?<!"),(?!")')
    event_data = []
    for event in scripts:
        e = event.string.\
            replace("\n", '').\
            replace("\t", '').\
            replace("\r", '').\
            replace("@", '').strip()
        e = re.sub(r'  +', '', e)
        e = re.sub(comma_hugged_by_quotes, "", e)
        e = e.replace('""', '", "')
        e = json.loads(e)
        event_data.append(e)
    
    return event_data


def get_event_websites(soup):
    events_divs = soup.find_all('div', {'class': 'event'})
    event_websites = [e.find('a', {}).get('href') for e in events_divs]
    
    return event_websites


def get_missing_locations(event_website, event_venue):
    if not event_venue:
        soup = soupify_page(event_website)
        ps_with_location = soup.find_all('p', {"style": "padding-left: 40px;"})
        missing_locations = []
        for p in ps_with_location:
            if p.find("em") is not None:
                p_text = p.find("em").text
                location = p_text.replace("Location:", "").split("–")[0].strip()
                missing_locations.append(location)
        return missing_locations


def schematize_event(event_data, event_websites):
    events = []
    n_missing_locations = 0
    for i, e in enumerate(event_data):
        event_name = e.get('name')
        event_website = event_websites[i]
        start_time, start_date = schematize_event_time(e.get('startDate'))
        end_time, end_date = schematize_event_time(e.get('endDate'))
        event_venue = e.get('location', {}).get('name')
        event_description = e.get('description')
        image = e.get('image', '')
        required = [
            event_name,
            event_website,
            start_date,
            event_venue,
            event_description
        ]
        missing_locations = get_missing_locations(event_website, event_venue)
        
        if not all(required):
            # might be a place with different venues at different times
            # although the times are updated by api, venues need to be scraped
            if not event_venue:
                event_venue = missing_locations[n_missing_locations]
                n_missing_locations += 1
            else:
                site = event_website
                msg = f"Unable to extract required data for ANS event: {site}"
                logger.error(msg, exc_info=True)
                continue

        event = {'Event Name': event_name,
                 'Event Website': event_website,
                 'Event Start Date': start_date,
                 'Event Start Time': start_time,
                 'Event End Date': end_date,
                 'Event End Time': end_time,
                 'Event Venue Name': event_venue,
                 'Timezone': 'America/New_York',
                 'Event Cost': '',
                 'Event Description': event_description,
                 'Event Organizers': 'Audubon Naturalist Society',
                 'Event Currency Symbol': '$',
                 'Event Category': '',
                 'Event Featured Image': image,
                 'All Day Event': False}
        events.append(event)
        
    return events


def schematize_event_time(event_time):
    '''
    Converts a time string like 2019-10-5T08-08-00-00.
    '''
    date, time = event_time.split("T")
    time = time[time.index("-") + 1:]

    try:
        time_obj = datetime.strptime(time, "%H-%M-%S")
        schematized_event_time = datetime.strftime(time_obj, "%H:%M:%S")
    except ValueError as e:
        msg = f'Exception schematizing {time}: {e}'
        logger.error(msg, exc_info=True)
        schematized_event_time = ''
        
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        schematized_event_date = datetime.strftime(date_obj, "%Y-%m-%d")
    except ValueError as e:
        msg = f'Exception schematizing this {date}: {e}'
        logger.error(msg, exc_info=True)
        schematized_event_date = ''
            
    return schematized_event_time, schematized_event_date


def post_outmonth(outmonth):
    url = 'https://anshome.org/wp-admin/admin-ajax.php'
    data = {'action': 'the_ajax_hook',
            'direction': 'none',
            'sort_by': 'sort_date',
            'filters[0][filter_type]': 'tax',
            'filters[0][filter_name]': 'event_type',
            'filters[0][filter_val]': '39',
            'shortcode[hide_past]': 'no',
            'shortcode[show_et_ft_img]': 'yes',
            'shortcode[event_order]': 'ASC',
            'shortcode[ft_event_priority]': 'no',
            'shortcode[lang]': 'L1',
            'shortcode[month_incre]': '0',
            'shortcode[only_ft]': 'no',
            'shortcode[hide_ft]': 'no',
            'shortcode[evc_open]': 'no',
            'shortcode[show_limit]': 'no',
            'shortcode[etc_override]': 'yes',
            'shortcode[show_limit_redir]': '0',
            'shortcode[tiles]': 'no',
            'shortcode[tile_height]': '0',
            'shortcode[tile_bg]': '0',
            'shortcode[tile_count]': '2',
            'shortcode[tile_style]': '0',
            'shortcode[members_only]': 'no',
            'shortcode[ux_val]': '1',
            'shortcode[show_limit_ajax]': 'no',
            'shortcode[show_limit_paged]': '1',
            'shortcode[hide_mult_occur]': 'no',
            'shortcode[show_repeats]': 'no',
            'shortcode[hide_end_time]': 'no',
            'shortcode[eventtop_style]': '0',
            'evodata[cyear]': f'{outmonth.strftime("%Y")}',
            'evodata[cmonth]': f'{outmonth.strftime("%m")}',
            'evodata[runajax]': '1',
            'evodata[evc_open]': '0',
            'evodata[cal_ver]': '2.7.3',
            'evodata[mapscroll]': 'true',
            'evodata[mapformat]': 'roadmap',
            'evodata[mapzoom]': '18',
            'evodata[ev_cnt]': '0',
            'evodata[show_limit]': 'no',
            'evodata[tiles]': 'no',
            'evodata[sort_by]': 'sort_date',
            'evodata[filters_on]': 'true',
            'evodata[range_start]': '0',
            'evodata[range_end]': '0',
            'evodata[send_unix]': '0',
            'evodata[ux_val]': '1',
            'evodata[accord]': '0',
            'evodata[rtl]': 'no',
            'ajaxtype': 'jumper'}
    try:
        r = requests.post(url, data=data)
        return r.json().get('content')
    except Exception as e:
        msg = f"Error requesting outmonth events for {outmonth} for ANS: {e}"
        logger.error(msg, exc_info=True)


def get_out_month_events():
    outmonths = []
    now = datetime.now()
    for i in range(1, 4):
        outmonths.append(now + timedelta(days=30 * i))
    outmonth_events = []
    for outmonth in outmonths:
        outmonth_content = post_outmonth(outmonth)
        soup = bs4.BeautifulSoup(outmonth_content, 'html.parser')
        event_data = get_event_data(soup)
        event_websites = get_event_websites(soup)
        events = schematize_event(event_data, event_websites)
        outmonth_events.extend(events)

    return outmonth_events


def main():
    soup = soupify_page()
    if not soup:
        return []
    event_data = get_event_data(soup)
    event_websites = get_event_websites(soup)
    events = schematize_event(event_data, event_websites)
    outmonth_events = get_out_month_events()
    events.extend(outmonth_events)

    return events


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()
    print(len(events))
