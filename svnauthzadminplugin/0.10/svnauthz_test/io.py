import unittest

from svnauthz.model import *
from svnauthz.io import *

class ParserTest(unittest.TestCase):
    def test_parse(self):
        r = AuthzFileReader()
        m = r.read("testdata")
        self.assertEquals(m.serialize().strip(),open("testdata","r").read().strip())
        
    def test_parse_mixed(self):
        r = AuthzFileReader()
        m = r.read("testdata-mixed")
        self.assertEquals(m.serialize().strip(),open("testdata","r").read().strip())