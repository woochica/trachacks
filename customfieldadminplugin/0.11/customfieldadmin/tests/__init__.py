# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2011 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from unittest import TestSuite, makeSuite

def test_suite():
    suite = TestSuite()
    from customfieldadmin.tests import api
    suite.addTest(makeSuite(api.CustomFieldApiTestCase))
    from customfieldadmin.tests import web_ui
    suite.addTest(makeSuite(web_ui.CustomFieldAdminPageTestCase))
    return suite

