# Plugin to remove TICKET_APPEND privileges for a predefined list of ticketIDs
# Copyright 2008 Daniel A. Atallah <datallah@pidgin.im>

import re

from trac.config import ListOption
from trac.core import *
from trac.web.main import IRequestFilter

__all__ = ['ReadOnlyTicketFilter']

class ReadOnlyTicketFilter(Component):
	"""
	A Request Filter to remove TICKET_APPEND privileges for a predefined
	   list of ticketIDs

	After enabling the plugin in your trac.ini: 

	  readonlyticket.* = enabled
	  
	Add a section with the list of tickets to make readonly 

	  [readonlyticket]
	  ticket_list = 5,10,15
	"""

	implements(IRequestFilter)

	ticket_list = ListOption('readonlyticket', 'ticket_list', '',
		doc="""List of tickets that should be considered Read-Only for 
		users that don't have the TICKET_ADMIN priviledge.""")

	# RequestFilter methods
	def match_request(self, req):
		return False

	def pre_process_request(self, req, handler):
		return handler

	def post_process_request(self, req, template, content_type):
		match = re.match(r'/ticket/([0-9]+)$', req.path_info)
		ticketid = None
		if match:
			ticketid = match.group(1)
		if ticketid and ticketid in self.ticket_list and \
				req.perm.has_permission('TICKET_APPEND') and \
				not req.perm.has_permission('TICKET_ADMIN'):
			req.perm.perms['TICKET_APPEND'] = False
			req.hdf['ticket.attach_href'] = 0
			req.hdf['trac.acl.TICKET_APPEND'] = 0
		return template, content_type

