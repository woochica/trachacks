
#
# This is the main test runner for all the TracSlimTimer unit tests.
#
# Be sure to run it with trac's version of Python e.g.:
#
#   /opt/trac/0.10.3/install/bin/python test_all.py
#
# The tests will probably take a little while (e.g. 10s) because they do some
# slow things like connecting to SlimTimer and various databases.
#

import unittest
import test_users
import test_slimtimer
import test_time_store
import test_reporter

suite=unittest.TestSuite()
suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(test_users))
suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(test_slimtimer))
suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(test_time_store))
suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(test_reporter))

unittest.TextTestRunner().run(suite)

