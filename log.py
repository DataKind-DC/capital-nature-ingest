import csv
from datetime import datetime
import io
import logging
import traceback

from utils.event_source_map import event_source_map


class CsvFormatter(logging.Formatter):
    
    def __init__(self):
        self.output = io.StringIO()
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
        record_name = record.name
        record_message = record.msg
        if record_name == '__main__':
            try:
                record_name = record_message[35:record_message.index(":")]
            except ValueError:
                # when the error message from __main__ doesn't have a colon
                record_name = "unknown"
        record_name = record_name.replace("events.", "")
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
