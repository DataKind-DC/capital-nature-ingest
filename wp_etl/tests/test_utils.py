import unittest
import datetime

from wp_etl.utils import parse_datetime

class DateParserTest(unittest.TestCase):
    pass


def create_date_test(data):
    def test_data_parsed(self):
        d = parse_datetime(data[0])
        if data[2][0] == True:
            self.assertEqual(d.year,data[1].year)
        else:
            self.assertNotEqual(d.year,data[1].year)
        if data[2][1] == True:
            self.assertEqual(d.month,data[1].month)
        else:
            self.assertNotEqual(d.month,data[1].month)
        if data[2][2] == True:
            self.assertEqual(d.day,data[1].day)
        else:
            self.assertNotEqual(d.day,data[1].day)
        if len(data[2])>3 and data[2][3] == True:
            self.assertEqual(d.hour,data[1].hour)
        elif len(data[2])>3:
            self.assertNotEqual(d.hour,data[1].hour)
        if len(data[2])>4 and data[2][4] == True:
            self.assertEqual(d.minute,data[1].minute)
        elif len(data[2])>4:
            self.assertNotEqual(d.minute,data[1].minute)
        if len(data[2])>5 and data[2][5] == True:
            self.assertEqual(d.second,data[1].second)
        elif len(data[2])>5:
            self.assertNotEqual(d.second,data[1].second)
    return test_data_parsed

dates = [
    ("2018-01-01", datetime.datetime(2018, 1, 1), [True, True, True]),
    ("2018-01-01", datetime.datetime(2019, 2, 2), [False, False, False]),
    ("2020-12-31", datetime.datetime(2020, 12, 31), [True, True, True]),
    ("2020-2-2", datetime.datetime(2020, 2, 2), [True, True, True]),
    ("2020-12-31", datetime.datetime(2020, 12, 31, 0, 0, 0), [True, True, True, True, True, True]),
    ("2020-12-31T23:32:04", datetime.datetime(2020, 12, 31, 23, 32, 4), [True, True, True, True, True, True]),
    ("2020-12-31T09:01:02", datetime.datetime(2020, 12, 31, 9, 1, 2), [True, True, True, True, True, True]),
    ("2020-12-31T9:1:4", datetime.datetime(2020, 12, 31, 9, 1, 4), [True, True, True, True, True, True]),
    ("2020-12-31T23:32:04", datetime.datetime(2020, 12, 31, 22, 12, 6), [True, True, True, False, False, False]),
    ("2018-11-17T08:00:00-04:00", datetime.datetime(2018, 11, 17, 8, 0, 0), [True, True, True, True, True, True]),
    ("2018-12-09T19:00:00Z", datetime.datetime(2018, 12, 9, 19, 0, 0), [True, True, True, True, True, True]),
]
for k, date_tuple in enumerate(dates):
    test_method = create_date_test(date_tuple)
    test_method.__name__ = "test_can_parse_date_%i" % k
    setattr(DateParserTest, test_method.__name__, test_method)