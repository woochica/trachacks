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

from trac.core import implements, Component
from trac.wiki import IWikiSyntaxProvider


class Mozilla(Component):

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        word = r"[\w'!]+"
        yield (r"(?:^|(?<=\W))(?:\*%s\*|/%s/|_%s_)(?:(?=\W)|$)" % ((word,)*3),
               lambda x, y, z: (y[0] == '*' and '<strong>%s</strong>' or
                                y[0] == '/' and '<em>%s</em>' or
                                '<span class="underline">%s</span>') % y[1:-1])

    def get_link_resolvers(self):
        return []
