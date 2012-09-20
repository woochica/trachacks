# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.test import EnvironmentStub, Mock
from trac.ticket.model import Ticket
from trac.util.translation import _

from trachours.hours import TracHoursPlugin

class HoursTicketManipulatorTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(
            enable=['trac.*', 'trachours.*'])
        self.hours_thp = TracHoursPlugin(self.env)

    def tearDown(self):
        pass

    def test_prepare_ticket_exists(self):
        req = ticket = fields = actions = {}
        self.assertEquals(None,
            self.hours_thp.prepare_ticket(req, ticket, fields, actions))

    def test_validate_ticket_negativevalue_returnstuple(self):
        req = {}
        self.env.config.set('ticket-custom', 'estimatedhours', 'text')
        ticket = Ticket(self.env)
        ticket['estimatedhours'] = '-1'
        self.assertTrue(ticket.get_value_or_default('estimatedhours'))
        msg = _("Please enter a positive value for Estimated Hours")
        self.assertEquals(msg, self.hours_thp.validate_ticket(req, ticket)[0][1])

    def test_validate_ticket_notanumber_returnstuple(self):
        req = {}
        self.env.config.set('ticket-custom', 'estimatedhours', 'text')
        ticket = Ticket(self.env)
        ticket['estimatedhours'] = 'a'
        msg = _("Please enter a number for Estimated Hours")
        self.assertEquals(msg, self.hours_thp.validate_ticket(req, ticket)[0][1])

    def test_validate_ticket_empty_setstozero(self):
        req = {}
        self.env.config.set('ticket-custom', 'estimatedhours', 'text')
        ticket = Ticket(self.env)
        ticket['estimatedhours'] = ''
        self.hours_thp.validate_ticket(req, ticket)
        self.assertEquals('0', ticket['estimatedhours'])

    def test_validate_ticket_fielddoesnotexist_returnstuple(self):
        req = {}
        ticket = Ticket(self.env)
        msg = _("""The field is not defined. Please check your configuration.""")
        self.assertEquals(msg, self.hours_thp.validate_ticket(req, ticket)[0][1])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HoursTicketManipulatorTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
