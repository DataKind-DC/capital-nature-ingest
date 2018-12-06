import datetime

def parse_datetime(s):
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S-04:00", "%Y-%m-%dT%H:%M:%S-05:00"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError("no valid datetime found")

def get_date(s):
    dt = parse_datetime(s)
    return dt.date()

def get_time(s):
    dt = parse_datetime(s)
    if dt.hour == 0:
        return None
    return dt.time()