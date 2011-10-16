# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest


def test_suite():
    suite = unittest.TestSuite()
    
    import tractags.tests.admin
    suite.addTest(tractags.tests.admin.test_suite())
    
    import tractags.tests.api
    suite.addTest(tractags.tests.api.test_suite())
    
    import tractags.tests.macros
    suite.addTest(tractags.tests.macros.test_suite())
    
    import tractags.tests.model
    suite.addTest(tractags.tests.model.test_suite())
    
    import tractags.tests.query
    suite.addTest(tractags.tests.query.test_suite())
    
    import tractags.tests.ticket
    suite.addTest(tractags.tests.ticket.test_suite())
    
    import tractags.tests.web_ui
    suite.addTest(tractags.tests.web_ui.test_suite())
    
    import tractags.tests.wiki
    suite.addTest(tractags.tests.wiki.test_suite())
    
    return suite


# Start test suite directly from command line like so:
#   $> PYTHONPATH=$PWD python tractags/tests/__init__.py
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

