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
                        
    def test_parse_comments(self):
        r1 = AuthzFileReader()
        r2 = AuthzFileReader()
        m1 = r1.read("testdata")
        m2 = r2.read("testdata-comments")
        self.assertEquals(m1.serialize().strip(),m2.serialize().strip())
