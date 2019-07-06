from os import path
import sys
import unittest
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from events.vnps import main
from utils import schema_test_required, schema_test_all, schema_test_types

class VNPSTestCase(unittest.TestCase):
    '''
    Test cases for VNPS events.
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_main(self):
        events = main()
        tests = [schema_test_required, schema_test_all, schema_test_types]
        for test in tests:
            with self.subTest(test = test):
                result = test(events)
                self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()