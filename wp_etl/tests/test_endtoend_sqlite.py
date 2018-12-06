import unittest

from wp_etl.csv_parser import CSVParser
from wp_etl.tests.testing_utilities import SqliteDatabaseLoader

class EndToEndLocalTest(unittest.TestCase):

    def test_end_to_end_runs(self):
        cp = CSVParser()
        cp.open("result.csv")
        cp.parse()

        dbl = SqliteDatabaseLoader()
        dbl.load_events(cp.parsed_events)
