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
from trac.wiki import IWikiSyntaxProvider


class Mozilla(Component):

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        word = r"[\w'!]+"
        def mozillate(fmt, match, fullmatch):
            expr = match[1:-1]
            if match[0] == '*':
                return tag.strong(expr)
            elif match[0] == '/':
                return tag.em(expr)
            else:
                return tag.span(expr, class_='underline')
        yield (r"(?:^|(?<=\W))(?:\*%s\*|/%s/|_%s_)(?:(?=\W)|$)" % ((word,)*3),
               mozillate)

    def get_link_resolvers(self):
        return []
