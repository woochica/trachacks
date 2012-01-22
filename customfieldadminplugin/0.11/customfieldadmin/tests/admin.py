# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2012 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest

from trac.perm import PermissionSystem, PermissionCache
from trac.test import EnvironmentStub, Mock
from trac.ticket.api import TicketSystem
from trac.web.api import RequestDone
from trac.web.href import Href

from customfieldadmin.admin import CustomFieldAdminPage

class CustomFieldAdminPageTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        ps = PermissionSystem(self.env)
        ps.grant_permission('admin', 'TICKET_ADMIN')
        self.plugin = CustomFieldAdminPage(self.env)

    def tearDown(self):
        if hasattr(self.env, 'destroy_db'):
            self.env.destroy_db()
        del self.env

    def test_create(self):
        _redirect_url = ''
        def redirect(url):
            _redirect_url = url
            raise RequestDone
        req = Mock(perm=PermissionCache(self.env, 'admin'),
                   authname='admin',
                   chrome={},
                   href=Href('/'),
                   redirect=redirect,
                   method='POST',
                   args={'add': True,
                         'name': "test",
                         'type': "textarea",
                         'label': "testing",
                         'format': "wiki",
                         'row': '9',
                         'columns': '42'})
        try:
            self.plugin.render_admin_panel(req, 'ticket', 'customfields', None)
        except RequestDone, e:
            self.assertEquals(
                    sorted(list(self.env.config.options('ticket-custom'))),
                    [(u'test', u'textarea'),
                     (u'test.cols', u'60'),
                     (u'test.format', u'wiki'),
                     (u'test.label', u'testing'),
                     (u'test.options', u''),
                     (u'test.order', u'1'),
                     (u'test.rows', u'5'),
                     (u'test.value', u'')])

    def test_add_optional_select(self):
        # http://trac-hacks.org/ticket/1834
        _redirect_url = ''
        def redirect(url):
            _redirect_url = url
            raise RequestDone
        req = Mock(perm=PermissionCache(self.env, 'admin'),
                   authname='admin',
                   chrome={},
                   href=Href('/'),
                   redirect=redirect,
                   method='POST',
                   args={'add': True,
                         'name': "test",
                         'type': "select",
                         'label': "testing",
                         'options': "\r\none\r\ntwo"})
        try:
            self.plugin.render_admin_panel(req, 'ticket', 'customfields', None)
        except RequestDone, e:
            self.assertEquals(
                    sorted(list(self.env.config.options('ticket-custom'))),
                    [(u'test', u'select'), (u'test.label', u'testing'),
                     (u'test.options', u'|one|two'), (u'test.order', u'1'),
                     (u'test.value', u'')])

    def test_apply_optional_select(self):
        # Reuse the added custom field that test verified to work
        self.test_add_optional_select()
        self.assertEquals('select', self.env.config.get('ticket-custom', 'test'))
        # Now check that details are maintained across order change
        # that reads fields, deletes them, and creates them again
        # http://trac-hacks.org/ticket/1834#comment:5
        _redirect_url = ''
        def redirect(url):
            _redirect_url = url
            raise RequestDone
        req = Mock(perm=PermissionCache(self.env, 'admin'),
                   authname='admin',
                   chrome={},
                   href=Href('/'),
                   redirect=redirect,
                   method='POST',
                   args={'apply': True,
                         'order_test': '2'})
        try:
            self.plugin.render_admin_panel(req, 'ticket', 'customfields', None)
        except RequestDone, e:
            self.assertEquals(
                    sorted(list(self.env.config.options('ticket-custom'))),
                    [(u'test', u'select'), (u'test.label', u'testing'),
                     (u'test.options', u'|one|two'), (u'test.order', u'2'),
                     (u'test.value', u'')])

