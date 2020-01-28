from datetime import datetime, timedelta
from os import path
import sys
import unittest
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from utils.formatters import unicoder, date_filter

class FormattersTestCase(unittest.TestCase):
    
    def setUp(self):
        self.maxDiff = None

    def tearDown(self):
        pass

    def test_unicoder(self):
        result = unicoder('test')
        expected = 'test'
        self.assertEqual(result, expected)

    def test_unicoder_apostrophe(self):
        result = unicoder('Weâ€™ll')
        expected = "We’ll"
        self.assertEqual(result, expected)

    def test_unicoder_dash(self):
        result = unicoder('Earth Day â€“ Monday Mini Camp')
        expected = "Earth Day – Monday Mini Camp"
        self.assertEqual(result, expected)

    def test_unicoder_empty(self):
        result = unicoder('Â')
        expected = ""
        self.assertEqual(result, expected)

    def test_unicoder_quotes(self):
        result = unicoder('â€œ')
        expected = '“'
        self.assertEqual(result, expected)

    def test_unicoder_accents(self):
        result = unicoder('áéíóúüñ¿¡')
        expected = 'áéíóúüñ¿¡'
        self.assertEqual(result, expected)

    def test_date_filter(self):
        good_date = datetime.now() + timedelta(10)
        bad_date = datetime.now() + timedelta(1000)
        good_date = good_date.strftime('%Y-%m-%d')
        bad_date = bad_date.strftime('%Y-%m-%d')
        data = [{'Event Start Date': good_date},
                {'Event Start Date': bad_date}]
        result = date_filter(data)
        expected = [{'Event Start Date': good_date}]
        self.assertEqual(result, expected)

    def test_date_filter_bad_values(self):
        data = [{'Event Start Date': 'bad date'}]
        result = date_filter(data)
        expected = []
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()