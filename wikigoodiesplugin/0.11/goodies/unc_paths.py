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


class UNCPathLink(Component):

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods

    _unc_path_regexp = r"!?\\\\[^\s\\]+(?:\\[^\s\\]*)*"
    
    def get_wiki_syntax(self):
        yield (self._unc_path_regexp,
               (lambda x, y, z:
                tag.a(y, href='file:///'+y.replace('\\', '/'))))

    def get_link_resolvers(self):
        return []
