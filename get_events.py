from datetime import datetime
import logging
import os

#import boto3

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

from events import ans, arlington, aws, casey_trees, city_blossoms, dc_audubon, \
                   eleventh_street, fairfax, fona, friends_of_kenilworth_gardens, montgomery, \
                   nova_parks, nps, potomac_conservancy, rcc, riverkeeper, sierra_club_md, sierra_club, \
                   tnc, us_botanic_garden, vnps
from log import CsvFormatter
from tests.utils import schema_test
from utils import formatters, reports

logger = logging.getLogger(__name__)


def get_events():
    '''
    Combines the events output of all the event scrapers.

    Returns:
        events (list): a list of dicts, with each dict representing a single event.
    '''
    event_sources = [ans, arlington, aws, casey_trees, city_blossoms, dc_audubon,
                     eleventh_street, fairfax, fona, friends_of_kenilworth_gardens, montgomery,
                     nova_parks, nps, potomac_conservancy, rcc, riverkeeper, sierra_club_md, sierra_club, \
                     tnc, us_botanic_garden, vnps]
    events = []
    for event_source in event_sources:
        try:
            source_events = event_source.main()
        except Exception as e:
            logger.critical(f'Exception getting events in {event_source.__name__}:  {e}',
                            exc_info=True)
            continue
        unicoded_source_events = [{k: formatters.unicoder(v) for k,v in i.items()} for i in source_events]
        for i, event in enumerate(unicoded_source_events):
            try:
                schema_test([event])
            except Exception as e:
                logger.error(f'Exception getting events in {event_source.__name__}:  {e}',
                             exc_info=True)
                unicoded_source_events.pop(i)
        events.extend(unicoded_source_events)

    return events

def create_log_file():
    log_dir = os.path.join(os.getcwd(),'logs')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    
    now = datetime.now().strftime("%m-%d-%Y")
    log_path = os.path.join(log_dir, f'log_{now}.csv')
    if os.path.exists(log_path):
        os.remove(log_path)
    
    return log_path

def main(is_local = True, bucket = None):
    events = get_events()
    events = formatters.tag_events_with_state(events)
    reports.make_reports(events, is_local, bucket)

    return events

if __name__ == '__main__':
    log_file = create_log_file()
    logging.basicConfig(level=logging.WARNING, filename=log_file)
    logging.root.handlers[0].setFormatter(CsvFormatter())
    
    events = main()
    
    print(f"Done scraping {len(events)} events!")
    print(f"You can find the logs here:  {log_file}")
    print("And you can find the data and scrape report in ./data/ and ./reports/, respectively.")