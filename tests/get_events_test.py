from os import path
import sys
import unittest
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
import get_events

class GetEventsTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_unicoder(self):
        result = get_events.unicoder('test')
        expected = 'test'
        self.assertEqual(result, expected)

    def test_unicoder_apostrophe(self):
        result = get_events.unicoder('Weâ€™ll')
        expected = "We’ll"
        self.assertEqual(result, expected)

    def test_unicoder_dash(self):
        result = get_events.unicoder('Earth Day â€“ Monday Mini Camp')
        expected = "Earth Day – Monday Mini Camp"
        self.assertEqual(result, expected)

    def test_unicoder_empty(self):
        result = get_events.unicoder('Â')
        expected = ""
        self.assertEqual(result, expected)

    def test_unicoder_quotes(self):
        result = get_events.unicoder('â€œ')
        expected = '“'
        self.assertEqual(result, expected)
        
if __name__ == '__main__':
    unittest.main()
