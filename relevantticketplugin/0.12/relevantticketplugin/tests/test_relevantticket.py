# -*- coding: utf-8 -*-

from relevantticket.relevantticket import RelevantTicketPlugin
from trac.test import EnvironmentStub
from trac.test import Mock
from unittest import TestCase

class TestRelevantTicketPlugin(TestCase):
    def setUp(self):
        self.env = EnvironmentStub()
        self.ticket = Mock(values=[])
        self.store = RelevantTicketPlugin(self.env)
        
    def test_ticket_created_normal1(self):
        pass
    
    def tearDown(self):
        pass