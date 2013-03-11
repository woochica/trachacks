# vim: set sw=4 et ts=4:
#
# -*- coding: utf-8 -*-
import sys
import os
import re
import unittest

from macro import *
from trac.wiki.formatter import Formatter, OneLinerFormatter

class ComponentManagerStub(object):
    components = {}

    def component_activated(self, dummy):
        pass

class ContextStub(object):
    def __init__(self):
        self.hints = {}

    def set_hints(self, **hints):
        self.hints.update(hints)

    def get_hint(self, name):
        if self.has_hint(name):
            return self.hints[name]
        else:
            return None

    def has_hint(self, name):
        return name in self.hints

    pass

class LogStub(object):
    def info(self, what):
        pass

class DbContextStub(object):
    def cursor(self):
        return DbCursorStub()

class EnvironmentStub(object):
    def __init__(self):
        self.log = LogStub()

    def get_db_cnx(self):
        return DbContextStub()

    def log(self, what):
        pass

class DbCursorStub():
    def __init__(self):
        self.description = []
        self.description.append(['n1'])

    def __iter__(self):
        return iter([])

    def execute(self, query, parameters):
        pass

class RequestStub(object):
    def __init__(self):
        self.authname = 'Me'

    def href(self, relative = ''):
        return "/my-project" + relative

    pass

class FormatterStub(object):
    pass

class JQChartMacroTest(unittest.TestCase):
    def setUp(self):
        self.formatter = FormatterStub()
        self.formatter.req = RequestStub()
        self.formatter.context = ContextStub()

        self.env = EnvironmentStub()

        self.chart = JQChartMacro(ComponentManagerStub())
        self.chart.env = self.env

    def test_render(self):
        rendered = self.chart.expand_macro(self.formatter, 'JQChart',
                '"query" : "select * from ticket"')

        self.assertTrue(re.search('renderChart', rendered, re.IGNORECASE))
        # self.assertTrue('title="my comment"' in rendered)
        
    def test_commas_in_comments(self):
        rendered = self.chart.expand_macro(self.formatter, 'JQChart', 
                '"query" : "select * from ticket"')

        self.assertTrue(re.search('renderChart', rendered, re.IGNORECASE))
        
if __name__ == '__main__':
    unittest.main()

