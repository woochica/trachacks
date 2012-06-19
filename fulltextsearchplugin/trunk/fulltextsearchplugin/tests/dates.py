import datetime
import unittest

from trac.util import datefmt

import mx.DateTime

from fulltextsearchplugin.dates import normalise_datetime

class DatesTestCase(unittest.TestCase):
    def setUp(self):
        self.correct_datetime = datetime.datetime(2001, 1, 2, 15, 45, 57,
                                                  tzinfo=datefmt.localtz)

    def test_normalise_date_none(self):
        self.assertEqual(None, normalise_datetime(None))

    def test_normalise_datetime(self):
        self.assertEqual(self.correct_datetime,
            normalise_datetime(datetime.datetime(2001, 1, 2, 15, 45, 57)))

    def test_normalise_datetime_w_tzinfo(self):
        self.assertEqual(self.correct_datetime,
                         normalise_datetime(self.correct_datetime))

    def test_normalise_mx_datetime(self):
        self.assertEqual(self.correct_datetime,
            normalise_datetime(mx.DateTime.DateTime(2001, 1, 2, 15, 45, 57)))



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DatesTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
