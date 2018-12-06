import datetime

def parse_datetime(s):
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S-04:00", "%Y-%m-%dT%H:%M:%S-05:00"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError("no valid datetime found for " + s)
