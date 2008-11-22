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

    #internal
    def _format_link(self, label, url):
        return tag.a(label, href=url)

    def _replace_url(self, url, regex, match):
      return re.sub(regex, url, match.group(0))

    # IWikiSyntaxProvider methods
    def get_link_resolvers(self):
        return []

    def get_wiki_syntax(self):
        for regex, url in self.regex_links:
            yield (regex, (lambda re:
                lambda formatter, ns, match:
                    self._format_link(match.group(0), self._replace_url(url, re, match)))(regex))
