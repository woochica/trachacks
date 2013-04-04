# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Steffen Hoffmann

import shutil
import tempfile
import unittest
from datetime import datetime

from trac.test import EnvironmentStub, Mock
from trac.ticket.model import Ticket
from trac.util.datefmt import utc


class TicketLinksTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                enable=['trac.*', 'mastertickets.*']
        )
        self.env.path = tempfile.mkdtemp()
        self.req = Mock()

        self.db = self.env.get_db_cnx()

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TicketLinksTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
