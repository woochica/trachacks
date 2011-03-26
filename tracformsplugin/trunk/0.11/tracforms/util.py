# -*- coding: utf-8 -*-

# 2011 Steffen Hoffmann

import htmlentitydefs
import re
import unittest

from codecs          import getencoder
from trac.util.text  import to_unicode


# code from an article published by Uche Ogbuji on 15-Jun-2005 at
# http://www.xml.com/pub/a/2005/06/15/py-xml.html
def xml_escape(text):
    enc = getencoder('us-ascii')
    return enc(to_unicode(text), 'xmlcharrefreplace')[0]


# adapted from code published by John J. Lee on 06-Jun-2007 at
# http://www.velocityreviews.com/forums
#   /t511850-how-do-you-htmlentities-in-python.html
unichresc_RE = re.compile(r'&#?[A-Za-z0-9]+?;')

def xml_unescape(text):
    return unichresc_RE.sub(_replace_entities, text)

def _unescape_charref(ref):
    name = ref[2:-1]
    base = 10
    # DEVEL: gain 20 % performance by omitting hex references (not used here)
    if name.startswith("x"):
        name = name[1:]
        base = 16
    return unichr(int(name, base))

def _replace_entities(match):
    ent = match.group()
    if ent[1] == "#":
        #return _unescape_charref(ent)
        return unichr(int(ent[2:-1], 10))
    repl = htmlentitydefs.name2codepoint.get(ent[1:-1])
    if repl is not None:
        repl = unichr(repl)
    else:
        repl = ent
    return repl


class UnescapeTests(unittest.TestCase):

    def test_unescape_charref(self):
        self.assertEqual(unescape_charref(u"&#38;"), u"&")
#        self.assertEqual(unescape_charref(u"&#x2014;"), u"\N{EM DASH}")
        self.assertEqual(unescape_charref(u"—"), u"\N{EM DASH}")

    def test_unescape(self):
        self.assertEqual(unescape(u"&amp; &lt; &mdash; — &#x2014;"),
            u"& < %s %s %s" % tuple(u"\N{EM DASH}"*3)
        )
        self.assertEqual(unescape(u"&a&amp;"), u"&a&")
        self.assertEqual(unescape(u"a&amp;"), u"a&")
        self.assertEqual(unescape(u"&nonexistent;"), u"&nonexistent;")

#    unittest.main()

