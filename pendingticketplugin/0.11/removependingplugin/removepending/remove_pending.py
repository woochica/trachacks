# Plugin to remove Pending status when the reporter modifies a ticket
# Copyright 2007-2008 Daniel A. Atallah <datallah@pidgin.im>

from datetime import datetime
from trac.core import *
from trac.ticket import Ticket, ITicketChangeListener
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.web_ui import TicketModule
from trac.attachment import IAttachmentChangeListener
from trac.util.datefmt import to_timestamp, utc

class RemovePendingPlugin(Component):
	implements (ITicketChangeListener, IAttachmentChangeListener)

	def ticket_created(self, ticket):
		pass

	def ticket_changed(self, ticket, comment, author, old_values):
		if (not old_values.has_key('pending')):
                	if (author == ticket['reporter'] and ticket['pending'] == '1'):
	                	self.env.log.info('Removing Pending status for ticket %s due to comment'
						  % (ticket.id))

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
	                        (ticket.id, to_timestamp(time_changed), author, 'pending', '1', '0'))

        	                db.commit();

	def ticket_deleted(self, ticket):
		pass

	def attachment_added(self, attachment):
		# Check whether we're dealing with a ticket resource
		resource = attachment.resource
		while resource:
			if resource.realm == 'ticket':
				break
			resource = resource.parent

		if (resource and resource.realm == 'ticket' and resource.id is not None):
			db = attachment.env.get_db_cnx();
			ticket = Ticket(attachment.env, resource.id, db)
                	if (attachment.author == ticket['reporter'] and ticket['pending'] == '1'):
	                	self.env.log.info('Removing Pending status for ticket %s due to attachment'
						  % (ticket.id))

				comment = 'Attachment (%s) added by ticket reporter.' % (attachment.filename)
				ticket['pending'] = '0'

				# determine sequence number...
				cnum = 0
				tm = TicketModule(self.env)
				for change in tm.grouped_changelog_entries(ticket, db):
					if change['permanent']:
		                                cnum += 1

				#We can't just use attachment.date as it screws up event sequencing
				now = datetime.now(utc)

				ticket.save_changes(attachment.author, comment, now, db, cnum + 1)
		                db.commit()

				#trigger notification since we've changed the ticket
                		tn = TicketNotifyEmail(self.env)
		                tn.notify(ticket, newticket=False, modtime=now)

	def attachment_deleted(self, attachment):
		pass

