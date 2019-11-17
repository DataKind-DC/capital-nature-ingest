import csv
from datetime import datetime
import io
import logging
import os
import re
import traceback

from utils.event_source_map import event_source_map


class CsvFormatter(logging.Formatter):
    def __init__(self):
        self.output = io.StringIO()
        self.writer = csv.writer(self.output, quoting=csv.QUOTE_ALL)
        self.writer.writerow(["Time", "Level", "Event Source", "Message", "Exc Info"])
        self.now = datetime.now().strftime("%m-%d-%Y")
        self.event_source_map = event_source_map

    def format(self, record):
        try:
            exc_type, exc_value, tb = record.exc_info
            tb = " ".join(traceback.format_tb(tb)).replace("\n",'').replace(",",'').strip()
            exc_info = f"{exc_type} {exc_value} {tb}"
        except (AttributeError, TypeError) as e:
            raise ValueError(f"{e} raised by logging formatter, likely becuase a logger didn't set exc_info=True")
        record_name = record.name
        record_message = record.msg
        if record_name == '__main__':
            record_name = record_message[35:record_message.index(":")] 
        record_name = record_name.replace("events.","")
        event_source = self.event_source_map[record_name]
        self.writer.writerow(
            [self.now, record.levelname, event_source, record_message, exc_info])
        data = self.output.getvalue()
        self.output.truncate(0)
        self.output.seek(0)
        
        return data.strip()
