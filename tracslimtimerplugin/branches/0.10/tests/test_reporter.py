
import sys
sys.path = ['..'] + sys.path

import unittest
import datetime
import logging
import os

from tracslimtimer import reporter, slimtimer, users, time_store
import testconfig

#
# Unit tests for tracslimtimer.reporter.Reporter
#
class ReporterTest(unittest.TestCase):

    def setUp(self):
        self.setUpST()
        self.setUpUsers()
        self.setUpStore()
        self.setUpLogger()

    #
    # A very simple test that tests nothing at all. It just checks we can
    # actually create a reporter object and call fetch_entries for the past
    # day.
    #
    def test_basic(self):
        rpt = reporter.Reporter(self.ts, self.st, self.users, self.logger)
        self.assertNotEqual(rpt, None)

        end = datetime.datetime.today()
        start = end - datetime.timedelta(days=1)
        rpt.fetch_entries(start, end)

    def setUpST(self):
        if self.__dict__.has_key('st'):
            return

        username = testconfig.get('slimtimer', 'username')
        password = testconfig.get('slimtimer', 'password')
        api_key  = testconfig.get('slimtimer', 'api_key')

        self.st = slimtimer.SlimTimerSession(username, password, api_key)

    def setUpUsers(self):
        if self.__dict__.has_key('users'):
            return

        config_file = testconfig.get('users', 'config_file')
        if not os.path.isfile(config_file):
            self.fail("User configuration file %s is not available"
                    % config_file)

        self.users = users.Users(config_file)

    def setUpStore(self):
        if self.__dict__.has_key('ts'):
            return

        db_host     = testconfig.get('database', 'host')
        db_user     = testconfig.get('database', 'username')
        db_password = testconfig.get('database', 'password')
        db_database = testconfig.get('database', 'database')

        self.ts = time_store.TimeStore(host = db_host,
                               user = db_user,
                               password = db_password,
                               database = db_database)

    def setUpLogger(self):
        if self.__dict__.has_key('logger'):
            return

        self.logger = logging.getLogger("ReporterTest")
        self.logger.addHandler(logging.StreamHandler())
        self.logger.setLevel(20)

if __name__ == '__main__':
    unittest.main()

