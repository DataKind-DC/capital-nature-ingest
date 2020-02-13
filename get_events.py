from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from inspect import getmodule
from io import StringIO
import logging
import os

from events import ans, arlington, aws, casey_trees, city_blossoms, \
    dc_audubon, eleventh_street, fairfax, fona, \
    friends_of_kenilworth_gardens, loudoun_wildlife_conservancy, \
    montgomery, nova_parks, nps, potomac_conservancy, rcc, riverkeeper, \
    sierra_club_md, sierra_club, tnc, us_botanic_garden, vnps, \
    nva_audubon_society
from log import CsvFormatter, create_log_file
from tests.utils import schema_test
from utils import formatters, reports, s3_utils

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

log_path, logger, log_file_name = create_log_file(BUCKET)


def get_source_events(event_source_main):
    f = getmodule(event_source_main).__name__.split('.')[-1]
    try:
        events = event_source_main()
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
        loudoun_wildlife_conservancy, montgomery, nova_parks,
        nps, potomac_conservancy, rcc, riverkeeper, sierra_club_md,
        sierra_club, tnc, us_botanic_garden, vnps, nva_audubon_society
    ]
    event_source_mains = [e.main for e in event_sources]

    with ThreadPoolExecutor(max_workers=len(event_sources)) as executor:
        events = executor.map(get_source_events, event_source_mains) 
    
    events = [item for sublist in events for item in sublist]
    
    return events


def main(event={}, context={}):
    try:
        events = get_events()
        reports.make_reports(events)
        if not BUCKET:
            return events
    except Exception as e:
        logger.critical(f"Critical error: {e}")
    finally:
        if BUCKET:
            logging.shutdown()
            log_data = log_path.getvalue()
            s3_utils.put_object(log_data, log_file_name)


if __name__ == '__main__':
    # only happens locally
    logging.basicConfig(level=logging.WARNING, filename=log_path)
    logging.root.handlers[0].setFormatter(CsvFormatter())

    events = main()

    print(f"Done scraping {len(events)} events!")
    print(f"You can find the logs here:  {log_path}")
    print("You can find the reports in ./data/ and ./reports/, respectively.")
