import unittest
from wanted_pages import *
from trac.test import EnvironmentStub
from trac.web.api import Request

class WantedPagesTestCase(unittest.TestCase):

    macro = None
    readmeText = ''
    req = None

    def setUp(self):
        env = EnvironmentStub()        
        self.macro = WantedPagesMacro(env)
        self.req = Request()
        
        readme = open('README')
        self.readmeText = readme.read()
        readme.close()

    def tearDown(self):
        self.macro = None

    def test_matches(self):
        links = self.macro.findBrokenLinks([self.readmeText], self.req)
        self.assertTrue('TimLowe' in links, 'TimLowe not found')
        self.assertTrue('TimLeo' in links, 'TimLeo not found')
        self.assertTrue('ParentWiki/SubWiki' in links, 'ParentWiki/SubWiki not found')
        self.assertTrue('NoSpaces' in links, 'NoSpaces not found')
        self.assertTrue('TimLowe5' in links, '[wiki:TimLowe5] not found')
        self.assertTrue('TimLowe6' in links, '[wiki:TimLowe6 link] not found')        

    def test_falseMatches(self):
        links = self.macro.findBrokenLinks([self.readmeText], self.req)
        self.assertFalse('!TimLewo' in links, '!TimLewo found')
        self.assertFalse('TimLoo' in links, '3TimLoo found')
        self.assertFalse('TimLee' in links, '`TimLee` found')        
        self.assertFalse('MyMacro' in links, '[[MyMacro] found')
        self.assertFalse('external' in links, '[wiki:http://external found')
        self.assertFalse('ExternalLink' in links, 'http://ExternalLink found')
        self.assertFalse('TomFool' in links, 'http://ExternalTrac/wiki/TomFool found')
        self.assertFalse('TimLow' in links, '{{{TimLow}}} found')
        self.assertFalse('MyClass' in links, '{{{if (MyClass)}}} found')
        self.assertFalse('WikiProcessor' in links, '[wiki:WikiProcessors WikiProcessor] found')
        self.assertFalse('PythonPath' in links, '{{{...PythonPath "sys.path + [\'/path/to/trac\']"...}}} found')
        self.assertFalse('IfModule' in links, '{{{...IfModule...}}} found')
        self.assertFalse('NestedBlocks' in links, '{{{...{{{ }}} NestedBlocks...}}} found')

def suite():
    return unittest.makeSuite(WantedPagesTestCase, 'test')

if __name__ == '__main__':
    unittest.main()
