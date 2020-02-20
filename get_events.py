from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from inspect import getmodule
from io import StringIO
import logging
from math import ceil
import os

from events import ans, arlington, aws, casey_trees, city_blossoms, \
    dc_audubon, eleventh_street, fairfax, fona, \
    friends_of_kenilworth_gardens, loudoun_wildlife_conservancy, lfwa, \
    montgomery, nova_parks, nps, potomac_conservancy, rcc, riverkeeper, \
    sierra_club_md, sierra_club, tnc, us_botanic_garden, vnps, \
    nva_audubon_society
from events.utils.log import get_logger
from tests.utils import schema_test
from events.utils import formatters, reports, aws_utils

try:
    NPS_KEY = os.environ['NPS_KEY']
except KeyError:
    NPS_KEY = input("Enter your NPS API key:")
    os.environ["NPS_KEY"] = NPS_KEY

try:
    EVENTBRITE_TOKEN = os.environ['EVENTBRITE_TOKEN']
except KeyError:
    EVENTBRITE_TOKEN = input("Enter your Eventbrite API key:")
    os.environ["EVENTBRITE_TOKEN"] = EVENTBRITE_TOKEN

BUCKET = os.getenv('BUCKET_NAME')

logger = get_logger(os.path.basename(__file__))


def get_source_events(event_source_main):
    f = getmodule(event_source_main).__name__.split('.')[-1]
    try:
        events = event_source_main()
        if not BUCKET:
            n = len(events)
            print(f"Scraped {n} event(s) for {f}")
    except Exception as e:
        msg = f'Exception getting events in {f}: {e}'
        logger.critical(msg, exc_info=True)
        return []
    events = [
        {k: formatters.unicoder(v) for k, v in i.items()}
        for i in events
    ]
    for i, event in enumerate(events):
        try:
            schema_test([event])
        except Exception as e:
            msg = f'Exception getting events in {f}: {e}'
            logger.error(msg, exc_info=True)
            events.pop(i)
    events = formatters.tag_events_with_state(events)
    
    return events


def get_events():
    '''
    Combines the events output of all the event scrapers.

    Returns:
        events (list): a list of dicts, w/ each dict being a single event.
    '''
    event_sources = [
        ans, arlington, aws, casey_trees, city_blossoms, dc_audubon,
        eleventh_street, fairfax, fona, friends_of_kenilworth_gardens,
        loudoun_wildlife_conservancy, lfwa, montgomery, nova_parks,
        nps, potomac_conservancy, rcc, riverkeeper, sierra_club_md,
        sierra_club, tnc, us_botanic_garden, vnps, nva_audubon_society
    ]
    event_source_mains = [e.main for e in event_sources]

    n_workers = ceil(len(event_sources) / 2)

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        events = executor.map(get_source_events, event_source_mains) 
    
    events = [item for sublist in events for item in sublist]
    
    return events


def main(event={}, context={}):
    try:
        events = get_events()
        if not BUCKET:
            return events
    except Exception as e:
        events = []
        logger.critical(f"Critical error: {e}")
    finally:
        log_df = reports.make_reports(events)
        if BUCKET:
            log_data = StringIO()
            log_df.to_csv(log_data, index=False)
            now = datetime.now().strftime("%m-%d-%Y")
            aws_utils.put_object(log_data.getvalue(), f'logs/log-{now}.csv')


if __name__ == '__main__':
    events = main()
    print(f"Done scraping {len(events)} events!")
    print(f"You can find the logs in ./logs")
    print("You can find the reports in ./data/ and ./reports/, respectively.")
