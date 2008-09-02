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

Copyright (c) 2007, 2008 Felix Tiede. All rights reserved.
Copyright (c) 2007, 2008 EyeC GmbH. All rights reserved.

TODO: Get me module documentation here! ASAP!
"""

__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__version__   = '0.11'

import re

from pkg_resources import resource_filename

from trac.core import *
from trac.mimeview.api import Context
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_ctxtnav, add_stylesheet, add_script
from trac.wiki.formatter import Formatter
#from trac.ticket.model import Ticket
from trac.util.html import html, Markup

from depgraph import DepGraphMacro

class DepGraphModule(Component):
	"""Provides a direct link to a ticket's dependency graph"""

	implements(IRequestFilter, IRequestHandler, ITemplateProvider)

	# IRequestFilter methods
	def pre_process_request(self, req, handler):
		return handler

	def post_process_request(self, req, template, data, content_type):
		if req.path_info.startswith('/ticket'):
			ticket_id = req.path_info[8:]
			add_ctxtnav(req, "Dependency Graph", req.href.depgraph(ticket_id), "Dependency Graph")

		return template, data, content_type

	# IRequestHandler methods
	def match_request(self, req):
		match = re.match(r'/depgraph/([0-9]+)$', req.path_info)
		if match:
			req.args['id'] = match.group(1)
			return True

	def process_request(self, req):
		req.perm.assert_permission('TICKET_VIEW')

		ticket = int(req.args.get('id'))
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		cursor.execute("SELECT 1 FROM ticket WHERE id=%s" %ticket)
		row = cursor.fetchone()
		if not row:
			raise TracError('Cannot build dependency graph for non-existent ticket %d.' % ticket)

#		req.hdf['title'] = "Ticket %s dependency graph" %ticket

		depth  = -1
		for key in req.args.keys():
			if key == 'depth':
				depth = req.args[key]
		
		data = {}

		context = Context.from_request(req, '')
		formatter = Formatter(self.env, context)
		graph = DepgraphMacro(self.env).expand_macro(formatter, 'DepGraph', \
				('%s,%s' %(ticket, depth)))
		data['ticket'] = "%s" %ticket
		data['depgraph'] = Markup(graph)
		add_ctxtnav(req, 'Back to Ticket #%s'%ticket, req.href.ticket(ticket))

		return 'depgraph.html', data, None
		
	# ITemplateProvider methods
	def get_templates_dirs(self):
		return [resource_filename(__name__, 'templates')]
		
	def get_htdocs_dirs(self):
		return [('depgraph', resource_filename(__name__, 'htdocs'))]
