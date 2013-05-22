# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.test import EnvironmentStub
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket

from trachours.hours import TracHoursPlugin
from trachours.setup import SetupTracHours
from trachours.ticket import TracHoursByComment

from trachours.tests import revert_trachours_schema_init


class TracHoursByCommentTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'trachours.*'])
        self.env.path = tempfile.mkdtemp()
        setup = SetupTracHours(self.env)
        setup.upgrade_environment(db=self.env.get_db_cnx())
        self.hours_thp = TracHoursPlugin(self.env)
        self.hours_thbc = TracHoursByComment(self.env)
        self.ticket_system = TicketSystem(self.env)

    def tearDown(self):
        self.env.reset_db()
        revert_trachours_schema_init(db=self.env.get_db_cnx())
        shutil.rmtree(self.env.path)

    def test_ticket_delete(self):
        ticket = Ticket(self.env)
        ticket['summary'] = 'ticket summary'
        ticket.insert()
        self.hours_thp.add_ticket_hours(ticket.id, 'user', 160)
        self.hours_thp.add_ticket_hours(ticket.id, 'user', 1200)

        ticket.delete()

        hours = self.hours_thp.get_ticket_hours(ticket.id)
        self.assertEqual([], hours)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TracHoursByCommentTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
