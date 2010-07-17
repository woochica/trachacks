from estimationtools.workloadchart import WorkloadChart
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.ticket.model import Ticket
from trac.web.href import Href
import unittest


class WorkloadChartTestCase(unittest.TestCase):
    
    def setUp(self):
        self.env = EnvironmentStub(default_data = True)
        self.env.config.set('ticket-custom', 'hours_remaining', 'text')
        self.env.config.set('estimation-tools', 'estimation_field', 'hours_remaining')
        self.req = Mock(href = Href('/'),
                        abs_href = Href('http://www.example.com/'),
                        perm = MockPerm(),
                        authname='anonymous')
       
    def _insert_ticket(self, estimation, owner):
        ticket = Ticket(self.env)
        ticket['summary'] = 'Test Ticket'
        ticket['owner'] = owner
        ticket['hours_remaining'] = estimation
        ticket['milestone'] = 'milestone1'
        return ticket.insert()

    def test_basic(self):
        workload_chart = WorkloadChart(self.env)
        self._insert_ticket('10', 'A')
        self._insert_ticket('20', 'B')
        self._insert_ticket('30', 'C')
        result = workload_chart.render_macro(self.req, "", "milestone=milestone1")
        self.assertEqual(result, u'<img src="http://chart.apis.google.com/chart?chs=400x100&amp;'\
                         'chf=bg,s,00000000&amp;chd=t:10,30,20&amp;cht=p3&amp;chtt=Workload 60h (1 workdays left)&amp;'\
                         'chl=A 10h|C 30h|B 20h&amp;chco=ff9900" alt=\'Workload Chart\' />')

    def test_invalid_value(self):
        workload_chart = WorkloadChart(self.env)
        self._insert_ticket('10', 'A')
        self._insert_ticket('10', 'B')
        self._insert_ticket('10', 'B')
        self._insert_ticket('30', 'C')
        self._insert_ticket('xxx', 'D')
        result = workload_chart.render_macro(self.req, "", "milestone=milestone1")
        self.assertEqual(result, u'<img src="http://chart.apis.google.com/chart?chs=400x100&amp;'\
                         'chf=bg,s,00000000&amp;chd=t:10,30,20&amp;cht=p3&amp;chtt=Workload 60h (1 workdays left)&amp;'\
                         'chl=A 10h|C 30h|B 20h&amp;chco=ff9900" alt=\'Workload Chart\' />' )
