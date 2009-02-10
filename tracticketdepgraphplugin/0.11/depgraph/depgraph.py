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
$Id$[[BR]]
$HeadURL$

Copyright (c) 2007-2009 Felix Tiede. All rights reserved.[[BR]]
Copyright (c) 2007-2009 EyeC GmbH. All rights reserved.

Thanks to andrei2102 for porting it to trac-0.11

= !DepGraph: The dependency graph for Trac =
Draw a dependency graph for a ticket with the specified recursion depth.

'''Note:''' Building a graph over all open tickets can lead to deadlocks of
the viewing browser, depending on how many tickets are open for the project in
question!

There is also support for [http://trac.edgewall.org/wiki/TracQuery Trac's query language].

== Usage ==
{{{
[[DepGraph]]                          # Produce a dependency graph for all tickets with infinite depth
[[DepGraph([<ticket id>][,<depth>])]] # Produce a dependency graph for the specified ticket (all, if empty) and the specified depth (infinite, if empty)

[[DepGraph(query:<ticket query>[,<depth>])]] # Produce a dependency graph for all tickets within the specified query.
}}}
"""

__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__version__   = '0.11'

from trac.core import *
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import wiki_to_html

from graphviz import Graphviz
from mastertickets.model import TicketLinks

from cgi import escape

class DepGraphMacro(WikiMacroBase):
	"""
	DepgraphMacro provides a plugin for Trac to render a dependency graph
	using graphviz for blocked tickets within a Trac wiki page.
	"""

	_maxdepth = -1		# Maximum depth for dependency graph
	_seen_tickets = []	# List of tickets already included
	_priorities = {}	# List of priorities in trac

	def _depgraph_all(self, req):
		"""
		Produces a dependency graph including all tickets, even those which
		do not block other tickets and are not blocked by other tickets
		"""
		result = ""
		db = self.env.get_db_cnx()
		cursor = db.cursor()

		sql = "SELECT id, priority, summary FROM ticket WHERE status != 'closed' ORDER BY id DESC;"
		cursor.execute(sql)
		tickets = cursor.fetchall()

		for ticket in tickets:
			links = TicketLinks(self.env, int(ticket[0]))
			blockers = links.blocked_by
			if len(blockers) == 0 and len(links.blocking) == 0:
				# Orphan ticket, not blocked and not blocking, skip
				continue

			bgcolor, border = self._get_color(str(ticket[1]))
			result += "\"" + str(ticket[0]) + "\" [ URL=\"" \
					+ req.href.ticket(int(ticket[0])) \
					+ "\" fontcolor=\"#bb0000\" fillcolor=\"" + bgcolor \
					+ "\" color=\"" + border \
					+ "\" tooltip=\"" + ticket[2].replace('"', '&quot;') \
					+ "\" ]\n"
			# Use blocked_by() from mastertickets.model.TicketLinks
			for blocker in blockers:
#				result += "\"%s\" -> \"%s\"" % (str(ticket[0]), str(blocker))
				result += "\"%s\" -> \"%s\"" % (str(blocker), str(ticket[0]))

		return result

	def _depgraph(self, req, base, depth):
		try:
			ticket = int(base)
		except ValueError:
			if base.startswith('query:'):
				base = base[6:]
			elif base.startswith('report:'):
				req.perm.assert_permission('REPORT_VIEW')

				db = self.env.get_db_cnx()
				cursor = db.cursor()
				cursor.execute('SELECT query FROM report WHERE id=%s;', 
								int(base[7:]))
				base = ''.join([line.strip() for line in cursor.splitlines()])
			else:
				raise TracError('Unknown ticket identifier.')

			from trac.ticket.query import Query
			query = Query.from_string(self.env, base, max=0) 
			return ''.join(self._depgraph(req, ticket['id'], -1) \
							for ticket in query.execute(req))

		self.log.debug('called depgraph(%s, %s)' % (str(ticket), str(depth)))
		if ticket in self._seen_tickets:
			return ''

		self._seen_tickets.append(ticket)
		links = TicketLinks(self.env, ticket)
		blockers = links.blocked_by
		if depth >= 0 and (len(blockers) == 0 and len(links.blocking) == 0):
			# Orphan ticket, not belonging to query, skip
			return ''

		db = self.env.get_db_cnx()
		cursor = db.cursor()
		sql = ("SELECT summary, priority FROM ticket WHERE id = %s;" \
				% (str(ticket)))
		cursor.execute(sql)
		summary, priority = cursor.fetchone()

		if depth == 0:
			bgcolor = "#cceecc"
			border  = "#00cc00"
		else:
			bgcolor, border = self._get_color(str(priority))

		depth = (depth > -1 and depth or 0)

		result = "\"" + str(ticket) + "\" [ URL=\"" \
				+ req.href.ticket(int(ticket)) \
				+ "\" fillcolor=\"" + bgcolor + "\" color=\"" + border \
				+ "\" fontcolor=\"#bb0000\" tooltip=\"" \
				+ summary.replace('"', '&quot;') + "\" ]\n"
		if self._maxdepth > 0 and depth >= self._maxdepth:
			return result
			
		# Use blocked_by() from mastertickets.model.TicketLinks
		blockers = TicketLinks(self.env, ticket).blocked_by
		for blocker in blockers:
			result += self._depgraph(req, int(blocker), depth+1)
#			result += "\"%s\" -> \"%s\"\n" % (str(ticket), str(blocker))
			result += "\"%s\" -> \"%s\"\n" % (str(blocker), str(ticket))

		return result

	def __init__(self):
		self.log.info('version: %s - id: %s' % (__version__, str(__id__)))

		from trac.ticket import Priority
		for priority in Priority.select(self.env):
			self._priorities[priority.name] = int(priority.value)

	def _get_color(self, priority):
		"""Set up background and border color for given priority"""

		try:
			int(priority)
		except ValueError:
			priority = self._priorities[priority]

		if priority == 1:
			bgcolor = "#ffddcc"
			border  = "#ee8888"
		elif priority == 2:
			bgcolor = "#ffffbb"
			border  = "#eeeeaa"
		elif priority == 3:
			bgcolor = "#f6f6f6"
			border  = "#cccccc"
		elif priority == 4:
			bgcolor = "#ddffff"
			border  = "#bbeeee"
		elif priority == 5:
			bgcolor = "#dde7ff"
			border  = "#ccddee"
		else:
			bgcolor = "#f6f6f6"
			border  = "#cccccc"
			
		return [bgcolor, border]

	def get_macros(self):
		"""Return an iterable that provides the names of the provided macros."""
		yield 'DepGraph'

	def get_macro_description(self, name):
		from inspect import getdoc, getmodule
		return getdoc(getmodule(self))

	def expand_macro(self, formatter, name, content):
		formatter.req.perm.assert_permission('TICKET_VIEW')

		self._seen_tickets = []
		options, kw = parse_args(content)
		if len(options) == 0:
			options = ['']

		# Generate graph header
#		result = "digraph G%s { rankdir = \"LR\"\n node [ style=filled ]\n" \
#				% (options[0])
		result = 'digraph G { rankdir = \"LR\"\n node [ style=filled ]\n'
		
		graphviz = Graphviz(self.env)

		if len(options) > 1 and options[1] is not '':
			self._maxdepth = int(options[1])

		if len(options) == 0 or (len(options) > 0 and options[0] == ''):
			result += self._depgraph_all(formatter.req)
		else:
			result += self._depgraph(formatter.req, options[0], 0)

		# Add footer
		result += "\n}"

		# Draw graph and return result to browser
		return graphviz.expand_macro(formatter, "graphviz", result)
