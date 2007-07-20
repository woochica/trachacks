# Plugin to remove Pending status when the reporter modifies a ticket
# Copyright 2007 Daniel A. Atallah <datallah@pidgin.im>

from trac.core import *
from trac.ticket import ITicketChangeListener

class RemovePendingPlugin(Component):
	implements (ITicketChangeListener)

	def ticket_created(self, ticket):
		pass

	def ticket_changed(self, ticket, comment, author, old_values):
		if (author == ticket['reporter'] and ticket['pending'] == '1' and not old_values.has_key('pending')):
			db, handle_ta = ticket._get_db_for_write(None)
			cursor = db.cursor()

			cursor.execute("UPDATE ticket_custom SET value = %s " \
				" WHERE ticket = %s AND name = %s ",
				('0', ticket.id, 'pending'))

			#Add the ticket change so that it will appear
			#correctly in the history and notifications
			cursor.execute("INSERT INTO ticket_change "
				"(ticket,time,author,field,oldvalue,newvalue) "
				"VALUES (%s, %s, %s, %s, %s, %s)",
			(ticket.id, ticket.time_changed, author, 'pending', '1', '0'))

			db.commit();

	def ticket_deleted(self, ticket):
		pass

