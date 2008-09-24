from estimationtools.hoursremaining import HoursRemaining
from trac.test import EnvironmentStub, Mock
from trac.ticket.model import Ticket
from trac.web.href import Href
import unittest


class BurndownChartTestCase(unittest.TestCase):
    
    def setUp(self):
        self.env = EnvironmentStub(default_data = True)
        self.env.config.set('ticket-custom', 'hours_remaining', 'text')
        self.env.config.set('estimation-tools', 'estimation_field', 'hours_remaining')
        self.req = Mock(href = Href('/'),
                        abs_href = Href('http://www.example.com/'),
                        perm = Mock(has_permission=lambda x: x == 'TICKET_VIEW'))
       
    def _insert_ticket(self, estimation):
        ticket = Ticket(self.env)
        ticket['summary'] = 'Test Ticket'
        ticket['hours_remaining'] = estimation
        ticket['milestone'] = 'milestone1'
        return ticket.insert()

    def test_basic(self):
        hoursRemaining = HoursRemaining(self.env)
        self._insert_ticket('10')
        self._insert_ticket('20')
        self._insert_ticket('30')
        result = hoursRemaining.render_macro(self.req, "", "milestone=milestone1")
        self.assertEqual(result, '60')

    def test_real(self):
        hoursRemaining = HoursRemaining(self.env)
        self._insert_ticket('10')
        self._insert_ticket('20.1')
        self._insert_ticket('30')
        result = hoursRemaining.render_macro(self.req, "", "milestone=milestone1")
        self.assertEqual(result, '60')

    def test_invalid(self):
        hoursRemaining = HoursRemaining(self.env)
        self._insert_ticket('10')
        self._insert_ticket('20')
        self._insert_ticket('30')
        self._insert_ticket('xxx')
        result = hoursRemaining.render_macro(self.req, "", "milestone=milestone1")
        self.assertEqual(result, '60')
