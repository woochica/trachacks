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
    suite.addTest(makeSuite(api.CustomFieldL10NTestCase))
    from customfieldadmin.tests import admin
    suite.addTest(makeSuite(admin.CustomFieldAdminPageTestCase))
    return suite

