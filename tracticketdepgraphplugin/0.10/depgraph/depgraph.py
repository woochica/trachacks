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

Copyright (c) 2007 Felix Tiede. All rights reserved.
Copyright (c) 2007 EyeC GmbH. All rights reserved.

= !DepGraph: The dependency graph for Trac =
Draw a dependency graph for a ticket with the specified recursion depth.

'''Note:''' Building a graph over all open tickets can lead to deadlocks of
the viewing browser, depending on how many tickets are open for the project in
question!

== Usage ==
{{{
[[DepGraph]]                          # Produce a dependency graph for all tickets with infinite depth
[[DepGraph([<ticket_id>][,<depth>])]] # Produce a dependency graph for the specified ticket (all, if empty) and the specified depth (infinite, if empty)
}}}
"""

__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__version__   = '0.10'

from util import get_color

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from graphviz import GraphvizMacro
from mastertickets.util import blocked_by

class DepgraphMacro(Component):
	"""
	DepgraphMacro provides a plugin for Trac to render a dependency graph
	using graphviz for blocked tickets within a Trac wiki page.
	"""
	implements(IWikiMacroProvider)

	_maxdepth = -1		# Maximum depth for dependency graph
	_seen_tickets = []	# List of tickets already included

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
			bgcolor, border = get_color(str(ticket[1]))
			result += "\"" + str(ticket[0]) + "\" [ URL=\"" \
					+ req.href.ticket(int(ticket[0])) \
					+ "\" fontcolor=\"#bb0000\" fillcolor=\"" + bgcolor \
					+ "\" color=\"" + border \
					+ "\" tooltip=\"" \
					+ ticket[2].encode('ascii', 'xmlcharrefreplace') + "\" ]\n"
			# Use blocked_by() from mastertickets.util
			blockers = blocked_by(self.env, int(ticket[0]))
			for blocker in blockers:
#				result += "\"%s\" -> \"%s\"" % (str(ticket[0]), str(blocker))
				result += "\"%s\" -> \"%s\"" % (str(blocker), str(ticket[0]))

		return result

	def _depgraph(self, req, ticket, depth):
		self.log.debug('called depgraph(%s, %s)' % (str(ticket), str(depth)))
		if ticket in self._seen_tickets:
			return ""

		self._seen_tickets.append(ticket)

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
			bgcolor, border = get_color(str(priority))

		result = "\"" + str(ticket) + "\" [ URL=\"" \
				+ req.href.ticket(int(ticket)) \
				+ "\" fillcolor=\"" + bgcolor + "\" color=\"" + border \
				+ "\" fontcolor=\"#bb0000\" tooltip=\"" \
				+ summary.encode('ascii', 'xmlcharrefreplace') + "\" ]\n"
		if self._maxdepth > 0 and depth >= self._maxdepth:
			return result
			
		# Use blocked_by() from mastertickets.util
		blockers = blocked_by(self.env, ticket)
		for blocker in blockers:
			result += self._depgraph(req, int(blocker), depth+1)
#			result += "\"%s\" -> \"%s\"\n" % (str(ticket), str(blocker))
			result += "\"%s\" -> \"%s\"\n" % (str(blocker), str(ticket))

		return result

	def __init__(self):
		self.log.info('version: %s - id: %s' % (__version__, str(__id__)))

	def get_macros(self):
		"""Return an iterable that provides the names of the provided macros."""
		yield 'DepGraph'

	def get_macro_description(self, name):
		from inspect import getdoc, getmodule
		return getdoc(getmodule(self))

	def render_macro(self, req, name, args):
		self._seen_tickets = []
		try:
			options = args.split(',')
		except:
			options = []

		# Generate graph header
		result = "digraph G%s { rankdir = \"LR\"\n node [ style=filled ]\n" \
				% (options[0])
		
		graphviz = GraphvizMacro(self.env)
		graphviz.load_config()

		if len(options) > 1 and options[1] is not '':
			self._maxdepth = int(options[1])

		if len(options) == 0 or (len(options) > 0 and options[0] == ''):
			result += self._depgraph_all(req)
		else:
			result += self._depgraph(req, int(options[0]), 0)

		# Add footer
		result += "\n}"

		# Draw graph and return result to browser
		return graphviz.render_macro(req, "graphviz", result)
