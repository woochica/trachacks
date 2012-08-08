# -*- coding: utf-8 -*-

import unittest

from trac.core import TracError
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.config import Option
from trac.util.compat import any, all
from trac.web.api import RequestDone
from trac.web.href import Href

from iniadmin.iniadmin import IniAdminPlugin


class IniAdminTestCase(unittest.TestCase):

    def setUp(self):
        def redirect(self):
            raise RequestDone

        self.env = EnvironmentStub(enable=[IniAdminPlugin])
        self.iniadmin = IniAdminPlugin(self.env)
        self.req = Mock(base_path='', chrome={}, method='GET', args={},
                        session={}, abs_href=Href('/'), href=Href('/'),
                        locale=None, perm=MockPerm(), authname=None, tz=None,
                        redirect=redirect)

    def tearDown(self):
        self.env.reset_db()

    def test_patterns_match_empty(self):
        match = self.iniadmin._patterns_match([u''])
        self.assertFalse(match('a'))
        self.assertFalse(match(u'あ'))
        self.assertFalse(match(u'sqlite:db/trac.db'))

    def test_patterns_match_wildcard(self):
        match = self.iniadmin._patterns_match([u'p??sword', u'passw**d'])
        self.assertFalse(match('a'))
        self.assertTrue(match('password'))
        self.assertTrue(match(u'páésword'))
        self.assertTrue(match('passwd'))
        self.assertTrue(match(u'passwod'))
        self.assertTrue(match(u'passwééééEéééééd'))

    def test_patterns_match_meta(self):
        match = self.iniadmin._patterns_match([u'pas.wo+d'])
        self.assertFalse(match('a'))
        self.assertTrue(match('pas.wo+d'))
        self.assertFalse(match(u'passwood'))

    def test_excludes(self):
        self.assertRaises(TracError, self.iniadmin.render_admin_panel,
                          self.req, 'tracini', 'iniadmin', '')

        template, data = self.iniadmin.render_admin_panel(
            self.req, 'tracini', 'trac', '')
        self.assertTrue(any(opt['name'] == 'database'
                            for opt in data['iniadmin']['options']))

    def test_passwords(self):
        template, data = self.iniadmin.render_admin_panel(
            self.req, 'tracini', 'trac', '')
        self.assertTrue(any(opt['type'] == 'password'
                            for opt in data['iniadmin']['options']
                            if opt['name'] == 'database'))

        template, data = self.iniadmin.render_admin_panel(
            self.req, 'tracini', 'notification', '')
        self.assertTrue(any(opt['type'] == 'password'
                            for opt in data['iniadmin']['options']
                            if opt['name'] == 'smtp_password'))

    def test_post_excludes(self):
        config = self.env.config
        excludes = self.env.config.get('iniadmin', 'excludes')

        self.req.method = 'POST'
        self.req.args['name'] = 'Updated via iniadmin'
        self.assertRaises(RequestDone,
                          self.iniadmin.render_admin_panel,
                          self.req, 'tracini', 'project', '')
        self.assertEqual('Updated via iniadmin', config.get('project', 'name'))

        self.req.method = 'POST'
        self.req.args['excludes'] = '***'
        self.assertRaises(TracError,
                          self.iniadmin.render_admin_panel,
                          self.req, 'tracini', 'iniadmin', '')
        self.assertEqual(excludes, config.get('iniadmin', 'excludes'))

    def test_option_doc_nonascii_ticket4179(self):
        option = Option('iniadmin-test', 'name', '', doc='résumé')
        template, data = self.iniadmin.render_admin_panel(
            self.req, 'tracini', 'iniadmin-test', '')
        self.assertTrue(all(type(opt['doc']) is unicode
                            for opt in data['iniadmin']['options']
                            if opt['name'] == 'name'))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IniAdminTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
