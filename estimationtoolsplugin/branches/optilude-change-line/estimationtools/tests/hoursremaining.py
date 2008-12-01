from estimationtools.hoursremaining import HoursRemaining
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.ticket.model import Ticket
from trac.web.href import Href
import unittest


class HoursRemainingTestCase(unittest.TestCase):
    
    def setUp(self):
        self.env = EnvironmentStub(default_data = True)
        self.env.config.set('ticket-custom', 'hours_remaining', 'text')
        self.env.config.set('estimation-tools', 'estimation_field', 'hours_remaining')
        self.req = Mock(href = Href('/'),
                        abs_href = Href('http://www.example.com/'),
                        perm = MockPerm(),
                        authname='anonymous')
       
    def _insert_ticket(self, estimation, status='open'):
        ticket = Ticket(self.env)
        ticket['summary'] = 'Test Ticket'
        ticket['hours_remaining'] = estimation
        ticket['milestone'] = 'milestone1'
        ticket['status'] = status
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

    def test_closed_tickets(self):
        hoursRemaining = HoursRemaining(self.env)
        self._insert_ticket('10')
        self._insert_ticket('20.1')
        self._insert_ticket('30')
        self._insert_ticket('30', status='closed')
        result = hoursRemaining.render_macro(self.req, "", "status!=closed, milestone=milestone1")
        self.assertEqual(result, '60')

    def test_to_many_tickets(self):
        hoursRemaining = HoursRemaining(self.env)
        for _ in range(200):
            self._insert_ticket('1')
        result = hoursRemaining.render_macro(self.req, "", "milestone=milestone1")
        self.assertEqual(result, '200')