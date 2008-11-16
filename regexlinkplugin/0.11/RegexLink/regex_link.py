"""
regex_link.py
====================

This is a plugin module for Trac.
  
Description:

  This is a wiki syntax provider to make links to external urls out of
  anything matching a user-defined regex.

Author:

  Roel Harbers

"""
import re
from trac.core import *
from trac.wiki import IWikiSyntaxProvider

class RegexLinkSyntaxProvider(Component):
    """Expands a user defined regex to a link.
    """
    implements(IWikiSyntaxProvider)

    #internal
    def _cb(self, formatter, ns, match):
        return '<a href="http://topdesk/query=' + match.group('topdesk1') + '%20' + match.group('topdesk2') + '">' + ns + '</a>'

    # IWikiSyntaxProvider methods
    def get_link_resolvers(self):
        return []

    def get_wiki_syntax(self):
# matches:
# 0001 000
# (1912 999)
# -0810 123!
# does not match:
# a0810 123
# 0810 123b
# 9912 123
# 0800 123
# 0813 123
# 0820 123
# 10813 123
# 0813 1234
# 813 123
        return [(r'\b(?P<topdesk1>[01]\d(?:0[1-9]|1[0-2])) (?P<topdesk2>\d{3})\b', self._cb)] # valid up to and including 2019
