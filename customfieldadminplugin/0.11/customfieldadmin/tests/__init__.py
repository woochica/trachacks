# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2011 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from unittest import TestSuite, makeSuite

def test_suite():
    suite = TestSuite()
    import customfieldadmin.tests.web_ui
    suite.addTest(makeSuite(
                customfieldadmin.tests.web_ui.CustomFieldAdminPageTestCase))
    return suite

