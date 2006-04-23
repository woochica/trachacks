# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Ciaran Jessup <ciaranj@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Ciaran Jessup <ciaranj@gmail.com>
import re

from trac.core import implements, Component
from trac.wiki import IWikiSyntaxProvider

class Bugzilla(Component):

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        yield ("#(?P<ticketid>\d+)", lambda x, y, z: self._format_symbol(z.group("ticketid")))

    def get_link_resolvers(self):
        return []

    def _format_symbol(self, i):
        bugzilla_url= self.env.config.get('bugzilla', 'bugzilla_url', 'http://bugzilla');
    	return "<a rel='nofollow' class='ticket' href='%s/show_bug.cgi?id=%s'>#%s</a>" % (bugzilla_url, i, i);
