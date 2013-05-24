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

from trac.test import EnvironmentStub

from dynfields.options import Options


class OptionsTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'dynfields.*'],
                                   path=tempfile.mkdtemp())
        self.env.config.filename = os.path.join(self.env.path, 'trac.ini')
        self.env.config['ticket-custom'].set('version.show_when_type',
                                             'enhancement')
        self.env.config['ticket-custom'].set('alwayshidden.clear_on_hide',
                                             False)
        self.env.config.save()

    def tearDown(self):
        self.env.reset_db()
        shutil.rmtree(self.env.path)

    def test_options(self):
        options = Options(self.env)
        self.assertEqual('enhancement', options['version.show_when_type'])
        self.assertEqual('False', options['alwayshidden.clear_on_hide'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(OptionsTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
