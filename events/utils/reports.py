import csv
from datetime import datetime
from io import StringIO
import os
import re
import sys

import pandas as pd
from pandas.errors import EmptyDataError

from .event_source_map import event_source_map
from .aws_utils import get_matching_s3_keys, object_key_exists, \
    read_and_delete_object, put_object


BUCKET = os.getenv('BUCKET_NAME')
if BUCKET:
    import boto3
    S3 = boto3.resource('s3')


def events_to_csv(events, out_dir='data', bucket=BUCKET):
    '''
    Write events to csv, either locally or to an S3 bucket.

    Parameters:
        events (list): a list of dicts, with each representing a single event.
        out_dir (str): dir to write file.
        bucket (str or None): the name of the S3 bucket. None by default

    Returns:
        scrape_file: location of file written to.
    '''
    scrape_date = datetime.now().strftime("%m-%d-%Y")
    filename = f'cap-nature-events-scraped-{scrape_date}.csv'
    fieldnames = {
        'Do Not Import', 'Event Name', 'Event Description', 'Event Excerpt',
        'Event Start Date', 'Event Start Time', 'Event End Date',
        'Event End Time', 'Timezone', 'All Day Event',
        'Hide Event From Event Listings', 'Event Sticky in Month View',
        'Feature Event', 'Event Venue Name',
        'Event Organizers', 'Event Show Map Link', 'Event Show Map',
        'Event Cost', 'Event Currency Symbol', 'Event Currency Position',
        'Event Category', 'Event Tags', 'Event Website',
        'Event Featured Image', 'Allow Comments',
        'Event Allow Trackbacks and Pingbacks'
    }

    if bucket:
        key = f'{out_dir}/{filename}'
        with StringIO() as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for event in events:
                writer.writerow(event)
            data = f.getvalue()
            put_object(data, key)
        return scrape_date
    else:
        out_path = os.path.join(os.getcwd(), out_dir, filename)
        if not os.path.exists(os.path.join(os.getcwd(), out_dir)):
            os.mkdir(os.path.join(os.getcwd(), out_dir))
        if sys.platform == 'win32':
            # https://stackoverflow.com/questions/3348460/csv-file-written-with-python-has-blank-lines-between-each-row
            with open(out_path, mode='w', encoding='utf-8', errors='ignore', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for event in events:
                    if event:
                        writer.writerow(event)
        else:
            with open(out_path, mode='w', encoding='utf-8', errors='ignore') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for event in events:
                    if event:
                        writer.writerow(event)
        return scrape_date


def get_past_venues(out_dir='data', bucket=BUCKET):
    '''
    Returns a set of event venues frm current venue csv in temp/ (if it exists)
    and then deletes that file (if it exists) as it will soon be replaced by 
    a new, more updated one.

    Parameters:
        out_dir (str): dir to write file.
        bucket (str or None): the name of the S3 bucket. None by default

    Returns:
        past_venues (set): set of venues, or an empty set if there are none
    '''
    venues = []
    if bucket:
        try:
            venue_key = next(get_matching_s3_keys(
                prefix='data/cap-nature-venues')
            )
        except StopIteration:
            return set()
        venue_file = read_and_delete_object(venue_key)
        with venue_file as f:
            reader = csv.reader(f)
            for i in reader:
                venue = i[0]
                venues.append(venue)
    else:
        data_path = os.path.join(os.getcwd(), out_dir)
        if not os.path.exists(data_path):
            os.mkdir(data_path)
        data_files = []
        for f in os.listdir(data_path):
            if os.path.isfile(os.path.join(data_path, f)) and 'venues-' in f:
                data_files.append(os.path.join(data_path, f))
        try:
            venue_file = data_files[0]
        except IndexError:
            # because there's no past file, so no past venues
            return set()
        with open(venue_file, errors='ignore') as f:
            reader = csv.reader(f)
            for i in reader:
                venue = i[0]
                venues.append(venue)
        os.remove(venue_file)
    
    past_venues = set(venues)
    past_venues.remove('VENUE NAME')
    
    return past_venues


def venues_to_csv(events, out_dir='data', bucket=BUCKET):
    '''
    Void function that writes unique event venues to csv, either locally or to
    an S3 bucket.

    Parameters:
        events (list): a list of dicts, with each representing a single event.
        out_dir (str): dir to write file.
        bucket (str or None): the name of the S3 bucket. None by default
    '''
    venues = []
    for event in events:
        event_venue = event['Event Venue Name']
        venues.append(event_venue)
    past_venues = get_past_venues()
    unique_venues = set(venues) | past_venues
    
    now = datetime.now().strftime("%m-%d-%Y")
    filename = f'cap-nature-venues-scraped-{now}.csv'
    
    if bucket:
        with StringIO() as f:
            writer = csv.writer(f)
            venues_to_write = list(unique_venues)
            venues_to_write.insert(0, 'VENUE NAME')
            for venue in venues_to_write:
                writer.writerow([venue])
            data = f.getvalue()
            key = f'{out_dir}/{filename}'
            put_object(data, key)

    else:
        out_path = os.path.join(os.getcwd(), out_dir, filename)
        if not os.path.exists(os.path.join(os.getcwd(), out_dir)):
            os.mkdir(os.path.join(os.getcwd(), out_dir))
        with open(out_path, mode='w', encoding='utf-8', errors='ignore') as f:
            writer = csv.writer(f)
            venues_to_write = list(unique_venues)
            venues_to_write.insert(0, 'VENUE NAME')
            for venue in venues_to_write:
                writer.writerow([venue])
    

def get_past_organizers(out_dir='data', bucket=BUCKET):
    '''
    Returns a set of event organizers from current organizer csv in temp/ 
    (if it exists) and then deletes that file (if it exists) as it will soon
    be replaced by a new, more updated one.

    Parameters:
        out_dir (str): dir to write file.
        bucket (str or None): the name of the S3 bucket. None by default

    Returns:
        past_organizers (set): set of organizers, or an empty set if none
    '''
    organizers = []
    if bucket:
        try:
            org_key = next(get_matching_s3_keys(
                prefix='data/cap-nature-organizer')
            )
        except StopIteration:
            return set()
        organizer_file = read_and_delete_object(org_key)
        with organizer_file as f:
            reader = csv.reader(f)
            for i in reader:
                organizer = i[0]
                organizers.append(organizer)
    else:
        data_path = os.path.join(os.getcwd(), out_dir)
        if not os.path.exists(data_path):
            os.mkdir(data_path)
        data_files = []
        for f in os.listdir(data_path):
            if 'organizers-' in f:
                data_files.append(os.path.join(data_path, f))
        try:
            organizer_file = data_files[0]
        except IndexError:
            # IndexError because there's no past file
            return set()
        with open(organizer_file) as f:
            reader = csv.reader(f)
            for i in reader:
                try:
                    organizer = i[0]
                except IndexError:
                    # file has no organizers for some other reason
                    return set()
                organizers.append(organizer)
        os.remove(organizer_file)
    
    past_organizers = set(organizers)
    past_organizers.remove('Event Organizer Name(s) or ID(s)')
    
    return past_organizers


def organizers_to_csv(events, out_dir='data', bucket=BUCKET):
    '''
    Void function that writes unique event organizers to csv, either locally 
    or to an S3 bucket.

    Parameters:
        events (list): a list of dicts, with each representing a single event.
        out_dir (str): dir to write file.
        bucket (str or None): the name of the S3 bucket. None by default.
    '''
    organizers = []
    for event in events:
        event_organizer = event['Event Organizers']
        organizers.append(event_organizer)
    past_organizers = get_past_organizers()
    unique_organizers = set(organizers) | past_organizers
    
    now = datetime.now().strftime("%m-%d-%Y")
    filename = f'cap-nature-organizers-scraped-{now}.csv'
    
    if bucket:
        with StringIO() as f:
            writer = csv.writer(f)
            orgs_to_write = list(unique_organizers)
            orgs_to_write.insert(0, 'Event Organizer Name(s) or ID(s)')
            for org in orgs_to_write:
                writer.writerow([org])
            data = f.getvalue()
            key = f'{out_dir}/{filename}'
            put_object(data, key)

    else:
        out_path = os.path.join(os.getcwd(), out_dir, filename) 
        if not os.path.exists(os.path.join(os.getcwd(), out_dir)):
            os.mkdir(os.path.join(os.getcwd(), out_dir))
    
        with open(out_path, mode='w', encoding='utf-8', errors='ignore') as f:
            writer = csv.writer(f)
            orgs_to_write = list(unique_organizers)
            orgs_to_write.insert(0, 'Event Organizer Name(s) or ID(s)')
            for org in orgs_to_write:
                writer.writerow([org])
            

class ScrapeReport():
    
    def __init__(self, events, scrape_date, bucket=BUCKET):
        self.bucket = bucket
        self.scrape_df = pd.DataFrame(events)
        if bucket:
            self.report_path = f'reports/scrape-report-{scrape_date}.csv'
        else:
            reports_dir = os.path.join(os.getcwd(), 'reports')
            if not os.path.exists(reports_dir):
                os.mkdir(reports_dir)
            self.report_path = os.path.join(
                reports_dir, 
                f'scrape-report-{scrape_date}.csv'
            )

        self.log_df  = ScrapeReport.get_log_df(scrape_date)
        
    @staticmethod
    def get_log_df(scrape_date):
        log_file = None
        global BUCKET
        root_dir = '/tmp' if BUCKET else os.getcwd()
        log_dir = os.path.join(root_dir, 'logs')
        
        log_dfs = []
        for f in os.listdir(log_dir):
            if not f.endswith('.csv'):
                continue
            f_base = os.path.basename(f)
            date_index = re.search(r'\d', f_base).start()
            log_date = f_base[date_index:].replace(".csv",'')
            if log_date == scrape_date:
                log_file = os.path.join(log_dir, f)
                try:
                    _log_df = pd.read_csv(log_file)
                except EmptyDataError:
                    # no errors logged in the file so delete it
                    os.remove(log_file)
                    continue
                log_dfs.append(_log_df)
        if log_dfs:
            log_df = pd.concat(log_dfs)
        else:
            # no errors logged in any files
            cols = ['Time', 'Level', 'Event Source', 'Message', 'Exc Info']
            log_df = pd.DataFrame(columns=cols)
        
        return log_df

    @staticmethod
    def prep_log_df(log_df):
        err_type_count_by_source = pd.DataFrame(
            log_df.groupby(
                by=['Event Source', 'Level']
            )['Time'].count()
        ).reset_index()
        cols = ['Event Organizers', 'Error Level', 'Number of Errors']
        err_type_count_by_source.columns = cols
        err_df = err_type_count_by_source.pivot(
            index='Event Organizers',
            columns='Error Level',
            values='Number of Errors'
        ).reset_index()
        
        return err_df   
    
    @staticmethod
    def prep_scrape_df(scrape_df):
        source_count = pd.DataFrame(scrape_df.groupby(
            by='Event Organizers')['Event Name'].count()).reset_index()
        source_count.columns = ['Event Organizers', 'Number of Events Scraped']
    
        return source_count
    
    @staticmethod
    def get_status(row):
        '''statuses can include
            # - broken
            #   - a single CRITICAL error
            #   - any presence in the logs AND no events found
            # - operational
            #   - events found and no errors
            # - operational but with errors
            #   - events found and at least one non-critical error
            # - operational but no events found
            #   - no errors and no events for the event source
        '''
        try:
            is_logged = int(row['Number of Errors'])
        except ValueError:
            is_logged = 0
        try:
            n_events = int(row['Number of Events Scraped'])
        except ValueError:
            n_events = 0
        try:
            n_crit = int(row['CRITICAL'])
        except (KeyError, ValueError):
            n_crit = 0
        if n_crit >= 1:
            return 'Broken'
        elif is_logged and not n_events:
            return 'Broken'
        elif not is_logged and n_events:
            return 'Operational'
        elif is_logged and n_events:
            return 'Operational, but with errors'
        else:
            return 'Status-determiner is broken'
    
    @staticmethod
    def append_nonevents(report_df):
        event_organizers = report_df['Event Organizers'].tolist()
        data = [report_df]
        n_err_cols = len(report_df.columns) - 4
        for _, v in event_source_map.items():
            if v not in event_organizers:
                new_row = [v, 0]
                for _ in range(n_err_cols):
                    new_row.append(0)
                new_row.extend([0, 'Operational, but no events found'])
                _df = pd.DataFrame(new_row).transpose()
                _df.columns = report_df.columns
                data.append(_df)

        df = pd.concat(data, axis=0).fillna(0)

        return df

    def make_scrape_report(self):
        '''Create an excel report based on data scraped and the logs'''
        err_df = ScrapeReport.prep_log_df(self.log_df)
        source_count = ScrapeReport.prep_scrape_df(self.scrape_df)
        report_df = pd.merge(source_count, err_df, how='outer')
        log_levels = ['CRITICAL', 'ERROR', 'WARNING']
        err_cols = [x for x in report_df.columns if x in log_levels]
        
        if not err_cols:
            report_df['Number of Errors'] = 0
        else:
            report_df['Number of Errors'] = report_df[err_cols].sum(axis=1)
        report_df['Status'] = report_df.apply(ScrapeReport.get_status, axis=1)
        df = ScrapeReport.append_nonevents(report_df)
        
        if self.bucket:
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            data = csv_buffer.getvalue()
            if object_key_exists(self.report_path):
                # Don't put the report if it already exists.
                # This makes the lambda idempotent for the lambda listening
                # for this PUT:object S3 event.
                pass
            else:
                put_object(data, self.report_path)
        else:
            df.dropna(inplace=True)
            df.to_csv(self.report_path, index=False)

        return self.log_df


def make_reports(events, bucket=BUCKET):
    scrape_date = events_to_csv(events)
    organizers_to_csv(events)
    venues_to_csv(events)
    sr = ScrapeReport(events, scrape_date)
    log_df = sr.make_scrape_report()
    
    return log_df
