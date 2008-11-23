"""
regex_link.py

====================

Copyright (C) 2008 Roel Harbers

 ----------------------------------------------------------------------------
 "THE BEER-WARE LICENSE" (Revision 42):
 Roel Harbers wrote this file. As long as you retain this notice you
 can do whatever you want with this stuff. If we meet some day, and you think
 this stuff is worth it, you can buy me a beer in return.
 ----------------------------------------------------------------------------

This is a plugin module for Trac.
  
Description:

  This is a wiki syntax provider to make links to external urls out of
  anything matching a user-defined regex.

Author:

  Roel Harbers

"""
import re
from genshi.builder import tag
from trac.core import *
from trac.wiki import IWikiSyntaxProvider

class RegexLinkSyntaxProvider(Component):
    """Expands a user defined regex to a link.
    """
    implements(IWikiSyntaxProvider)

    SECTION_NAME = 'regexlink'
    REGEX_PREFIX = 'regex'
    URL_PREFIX = 'url'

    def __init__(self):
        self.regex_links = []
        for option in self.config.options(self.SECTION_NAME):
            m = re.match(self.REGEX_PREFIX + r"(?P<id>[1-9]\d*)", option[0])
            if m != None:
                id = m.group('id')
                regex = option[1]
                url = self.config.get(self.SECTION_NAME, self.URL_PREFIX + id)
                self.regex_links += [(regex, url)]

    def _replace_url(self, url, regex, match):
      return re.sub(regex, url, match.group(0))

    # IWikiSyntaxProvider methods
    def get_link_resolvers(self):
        return []

    def get_wiki_syntax(self):
        for regex, url in self.regex_links:
            yield (regex, (lambda re, u:
                lambda formatter, ns, match:
                    formatter._make_ext_link(self._replace_url(u, re, match), match.group(0)))(regex, url))
