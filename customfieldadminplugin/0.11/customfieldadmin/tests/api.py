# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2012 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest

from trac.test import EnvironmentStub, Mock

from customfieldadmin.api import CustomFields

class CustomFieldApiTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.cf_api = CustomFields(self.env)

    def tearDown(self):
        if hasattr(self.env, 'destroy_db'):
            self.env.destroy_db()
        del self.env

    def test_systeminfo(self):
        try:
            from trac.loader import get_plugin_info
            # From ~0.12, Trac handles plugins and versions - no need to test
            return
        except ImportError:
            self.assertTrue(('CustomFieldAdmin',
                __import__('customfieldadmin', ['__version__']).__version__) \
                    in self.env.systeminfo)

    def test_delete_unknown_options(self):
        cf = customfield = {'name': 'foo', 'type': 'text', 'label': 'Foo'}
        self.cf_api.create_custom_field(cf)
        self.assertEquals('text',
                    self.env.config.get('ticket-custom', 'foo'))
        self.assertEquals('Foo',
                    self.env.config.get('ticket-custom', 'foo.label'))
        self.env.config.set('ticket-custom', 'foo.answer', '42')
        self.cf_api.delete_custom_field(cf, modify=False)
        self.assertEquals('',
                    self.env.config.get('ticket-custom', 'foo'))
        self.assertEquals('',
                    self.env.config.get('ticket-custom', 'foo.label'))
        self.assertEquals('',
                    self.env.config.get('ticket-custom', 'foo.answer'))

    def test_not_delete_unknown_options_for_modify(self):
        cf = customfield = {'name': 'foo', 'type': 'text', 'label': 'Foo'}
        self.cf_api.create_custom_field(cf)
        self.assertEquals('text',
                    self.env.config.get('ticket-custom', 'foo'))
        self.assertEquals('Foo',
                    self.env.config.get('ticket-custom', 'foo.label'))
        self.env.config.set('ticket-custom', 'foo.answer', '42')
        self.cf_api.delete_custom_field(cf, modify=True)
        self.assertEquals('',
                    self.env.config.get('ticket-custom', 'foo'))
        self.assertEquals('',
                    self.env.config.get('ticket-custom', 'foo.label'))
        self.assertEquals('42',
                    self.env.config.get('ticket-custom', 'foo.answer'))

class CustomFieldL10NTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.cf_api = CustomFields(self.env)

    def tearDown(self):
        if hasattr(self.env, 'destroy_db'):
            self.env.destroy_db()
        del self.env

    def test_translation_function(self):
        from customfieldadmin.api import _
        self.assertEquals('foo bar', _("foo bar"))
        self.assertEquals('foo bar', _("foo %(bar)s", bar='bar'))

    def test_translation_function_tag(self):
        from customfieldadmin.api import tag_
        from genshi.builder import tag
        self.assertEquals('<p>foo bar</p>', str(tag_(tag.p('foo bar'))))
        self.assertEquals('<p>foo bar</p>',
                    str(tag_(tag.p('foo %(bar)s' % {'bar': 'bar'}))))
