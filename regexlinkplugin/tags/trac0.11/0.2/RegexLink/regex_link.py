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
from trac.core import *
from trac.wiki import IWikiSyntaxProvider
from model import RegexLinkInfo

class RegexLinkSyntaxProvider(Component):
    """ Expands a user defined regex to a link
    """
    implements(IWikiSyntaxProvider)

    SECTION_NAME = 'regexlink'
    REGEX_PREFIX = 'regex'
    URL_PREFIX = 'url'

    def __init__(self):
        """ read configuration from trac.ini
        """
        self.regex_links = []
        for option in self.config.options(self.SECTION_NAME):
            m = re.match(self.REGEX_PREFIX + r"(?P<id>[1-9]\d*)", option[0])
            if m != None:
                id = m.group('id')
                regex = option[1]
                url = self.config.get(self.SECTION_NAME, self.URL_PREFIX + id)
                self.regex_links += [RegexLinkInfo(regex, url)]

    def get_link_resolvers(self):
        """ IWikiSyntaxProvider method
        """
        return []

    def get_wiki_syntax(self):
        """ IWikiSyntaxProvider method
        """
        for regex_link in self.regex_links:
            yield (regex_link.wiki_syntax_regex, (lambda rli:
                lambda formatter, ns, match:
                    formatter._make_ext_link(rli.replace_url(match), match.group(0)))(regex_link))
