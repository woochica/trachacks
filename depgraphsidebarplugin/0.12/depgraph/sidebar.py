# This file is part of TracTicketDepgraph.
#
# TracTicketDepgraph is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# TracTicketDepgraph is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Felix Tiede

"""
$Id$
$HeadURL$

Copyright (c) 2007-2009 Felix Tiede. All rights reserved.
Copyright (c) 2007-2009 EyeC GmbH. All rights reserved.

TODO: Get me module documentation here! ASAP!
"""

from pkg_resources import resource_filename

from ticketsidebarprovider.interface import ITicketSidebarProvider
from trac.core import *
from trac.mimeview.api import Context
from trac.web.chrome import ITemplateProvider, Chrome
from trac.wiki.formatter import Formatter
from trac.util.html import html, Markup
from trac.util.compat import set, sorted, partial

from depgraph import DepGraphMacro

from mastertickets.web_ui import MasterTicketsModule

class DepGraphSidebar(MasterTicketsModule):
    """Provides a sidebar with ticket's dependency graph"""

    implements(ITicketSidebarProvider, ITemplateProvider)

    def enabled(self, req, ticket):
        return ticket.id and req.authname

    def content(self, req, ticket):
        data = {'headline': 'Dependency Graph for Ticket #%s' %ticket.id }
        data['tkt'] = ticket
        g = self._build_graph(req, ticket.id)
        data['graph'] = g
        data['graph_render'] = partial(g.render, self.dot_path)
        data['use_gs'] = self.use_gs
        data['path'] = req.href.depgraph(ticket.id)
        return Chrome(self.env).load_template('depgraph-sidebar.html').generate(**data)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('depgraph', resource_filename(__name__, 'htdocs'))]
