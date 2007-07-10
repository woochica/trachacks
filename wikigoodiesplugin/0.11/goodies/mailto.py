# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Christian Boos <cboos@neuf.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Christian Boos <cboos@neuf.fr>

from genshi.builder import tag

from trac.core import implements, Component
from trac.web.chrome import Chrome
from trac.wiki import IWikiSyntaxProvider

class MailToLink(Component):

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods

    _email_regexp = r"!?<[^@]+@[^>]+>"
    
    def get_wiki_syntax(self):
        chrome = Chrome(self.env)
        def mailto(formatter, match, fullmatch):
            return tag.a(chrome.format_author(formatter.req, match),
                         href="mailto:"+match[1:-1])
        yield (self._email_regexp, mailto)

    def get_link_resolvers(self):
        return []
