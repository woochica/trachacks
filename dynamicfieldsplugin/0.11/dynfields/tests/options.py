# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
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
        self.env.config.filename = os.path.join(self.env.path, 'trac.ini')

    def tearDown(self):
        self.env.reset_db()
        shutil.rmtree(self.env.path)

    def test_options(self):
        self.env.config['ticket-custom'].set('version.show_when_type',
                                             'enhancement')
        self.env.config['ticket-custom'].set('alwayshidden.clear_on_hide',
                                             False)
        self.env.config.save()
        options = Options(self.env)

        self.assertEqual('enhancement', options['version.show_when_type'])
        self.assertEqual('False', options['alwayshidden.clear_on_hide'])

    def test_options_inherit(self):
        inherited_config = Configuration(os.path.join(self.env.path,
                                                      'global_trac.ini'))
        inherited_config['ticket-custom'].set('version.show_when_type',
                                              'enhancement')
        inherited_config['ticket-custom'].set('alwayshidden.clear_on_hide',
                                              False)
        inherited_config.save()
        self.env.config.parents.append(inherited_config)
        self.env.config['inherit'].set('file', inherited_config.filename)
        self.env.config.save()
        options = Options(self.env)

        self.assertEqual('enhancement', options['version.show_when_type'])
        self.assertEqual('False', options['alwayshidden.clear_on_hide'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(OptionsTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
