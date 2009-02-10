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
from trac.util.html import html, Markup

from genshi.builder import tag

from depgraph import DepGraphMacro

class DepGraphModule(Component):
	"""Provides a direct link to a ticket's dependency graph"""

	implements(IRequestFilter, IRequestHandler, ITemplateProvider)

	def _unescape(self, match):
		return chr(int(match.group(0)[1:], 16))

	# IRequestFilter methods
	def pre_process_request(self, req, handler):
		return handler

	def post_process_request(self, req, template, data, content_type):
		from mastertickets.model import TicketLinks
		if req.path_info.startswith('/ticket'):
			ticket_id = req.path_info[8:]
			links = TicketLinks(self.env, ticket_id)
			if len(links.blocked_by) > 0:
				depgraph_href = req.href.depgraph(ticket_id)
			else:
				depgraph_href = None
			add_ctxtnav(req, "Dependency Graph", depgraph_href,
						"Dependency Graph")
		if req.path_info.startswith('/query'):
			query = {}
			percent_enc = re.compile('\%[0-9a-fA-F]')
			for line in data['query'].to_string().splitlines():
				if '=' in line:
					if line.startswith('query:?'):
						line = line[7:]
					line = re.sub(percent_enc, self._unescape, line)
					key, value = line.split('=')
					if key in query:
						query[key].append(value)
					else:
						query[key] = [value]

			add_ctxtnav(req, tag.a('Dependency Graph',
							href=req.href('depgraph', **query)))

		return template, data, content_type

	# IRequestHandler methods
	def match_request(self, req):
		match = re.match(r'/depgraph/([0-9]+)$', req.path_info)
		if match:
			req.args['id'] = match.group(1)
			return True
		else:
			return req.path_info == '/depgraph'

	def process_request(self, req):
		req.perm.assert_permission('TICKET_VIEW')

		if 'id' in req.args.keys():
			try:
				ticket = int(req.args.get('id'))
			except ValueError:
				raise TracError('Need integer ticket id.')

			sql = ("SELECT 1 FROM ticket WHERE id=%s" %ticket)
		
			db = self.env.get_db_cnx()
			cursor = db.cursor()
			cursor.execute(sql)
			row = cursor.fetchone()
			if not row:
				raise TracError('Cannot build dependency graph for non-existent ticket %d.' % ticket)

			depth  = -1
			for key in req.args.keys():
				if key == 'depth':
					depth = req.args[key]

			options = '%s,%s' %(ticket, depth)
			add_ctxtnav(req, 'Back to Ticket #%s'%ticket,
							req.href.ticket(ticket))
			title = 'Ticket #%s Dependency Graph' %ticket
			headline = 'Dependency Graph for Ticket #%s' %ticket
		else:
			constraints = {}
			for key in req.args.keys():
				if isinstance(req.args[key], (list, tuple)):
					constraints[key] = '|'.join(req.args[key])
				else:
					constraints[key] = req.args[key]
			options = 'query:' + '&'.join(key + '=' +
						constraints[key] for key in constraints)

			title = 'Ticket query Dependency Graph'
			headline = 'Dependency Graph for Query'
			add_ctxtnav(req, 'Back to query', req.href('query', **req.args))
		
		data = {}

		context = Context.from_request(req, '')
		formatter = Formatter(self.env, context)
		graph = DepGraphMacro(self.env).expand_macro(formatter,
					'DepGraph', options)
		data['title'] = title
		data['headline'] = headline
		data['depgraph'] = Markup(graph)

		return 'depgraph.html', data, None
		
	# ITemplateProvider methods
	def get_templates_dirs(self):
		return [resource_filename(__name__, 'templates')]
		
	def get_htdocs_dirs(self):
		return [('depgraph', resource_filename(__name__, 'htdocs'))]
