# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.config import Configuration
from trac.test import EnvironmentStub

from dynfields.options import Options


class OptionsTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'dynfields.*'],
                                   path=tempfile.mkdtemp())

    def tearDown(self):
        self.env.reset_db()
        shutil.rmtree(self.env.path)

    def test_options(self):
        self.env.config['ticket-custom'].set('version.show_when_type',
                                             'enhancement')
        self.env.config['ticket-custom'].set('alwayshidden.clear_on_hide',
                                             False)
        options = Options(self.env)

        self.assertEqual('enhancement', options['version.show_when_type'])
        self.assertEqual('False', options['alwayshidden.clear_on_hide'])

    def test_options_inherit(self):
        inherited_config = Configuration('')
        inherited_config['ticket-custom'].set('version.show_when_type',
                                              'enhancement')
        inherited_config['ticket-custom'].set('alwayshidden.clear_on_hide',
                                              False)
        self.env.config.parents.append(inherited_config)
        options = Options(self.env)

        self.assertEqual('enhancement', options['version.show_when_type'])
        self.assertEqual('False', options['alwayshidden.clear_on_hide'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(OptionsTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
