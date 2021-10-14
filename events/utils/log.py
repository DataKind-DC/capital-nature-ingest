import csv
from datetime import datetime
from io import StringIO
import logging
import os
import sys
import traceback

from .event_source_map import event_source_map

BUCKET = os.getenv('BUCKET_NAME')

class CsvFormatter(logging.Formatter):
    
    def __init__(self):
        self.output = StringIO()
        self.writer = csv.writer(self.output, quoting=csv.QUOTE_ALL)
        cols = ["Time", "Level", "Event Source", "Message", "Exc Info"]
        self.writer.writerow(cols)
        self.now = datetime.now().strftime("%m-%d-%Y")
        self.event_source_map = event_source_map

    def format(self, record):
        try:
            exc_type, exc_value, tb = record.exc_info
            tb = " ".join(traceback.format_tb(tb))
            tb = tb.replace("\n", '').replace(",", '').strip()
            exc_info = f"{exc_type} {exc_value} {tb}"
        except (AttributeError, TypeError) as e:
            msg = f"{e} in log formatter, likely b/c exc_info!=True"
            raise ValueError(msg)
        record_message = record.msg
        record_name = record.name
        if record_name == 'get_events.py':
            record_name = record_message[28:record_message.index(":")]
        record_name = record_name.replace(".py","")
        event_source = self.event_source_map.get(record_name, record_name)
        self.writer.writerow([
            self.now,
            record.levelname,
            event_source,
            record_message,
            exc_info]
        )
        data = self.output.getvalue()
        self.output.truncate(0)
        self.output.seek(0)
        
        return data.strip()


def get_logger(event_source, bucket=BUCKET):
    logger = logging.getLogger(event_source)
    now = datetime.now().strftime("%m-%d-%Y")
    
    if bucket:
        log_dir = os.path.join("/tmp", "logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
    else:
        log_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
    if sys.platform != 'win32':
        log_file = os.path.join(log_dir, f'{event_source}_{now}.csv')   
        log_file = log_file.replace(".py", "")
        f_handler = logging.FileHandler(log_file)
        f_handler.setLevel(logging.WARNING)
        f_handler.setFormatter(CsvFormatter())
        logger.addHandler(f_handler)
    else:
        logger.disabled = True

    return logger