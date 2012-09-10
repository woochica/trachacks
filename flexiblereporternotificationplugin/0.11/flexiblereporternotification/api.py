# -*- coding: utf-8 -*-

from trac.ticket.api import ITicketActionController, TicketSystem
from trac.ticket.default_workflow import ConfigurableTicketWorkflow
import trac.ticket.notification as note

def get_recipients(self, tktid):
    
    notify_reporter = self.config.getbool('notification',
                                          'always_notify_reporter')
    notify_owner = self.config.getbool('notification',
                                       'always_notify_owner')
    notify_updater = self.config.getbool('notification',
                                         'always_notify_updater')
    for_reporting = self.config.getlist('notification', 'reporter_states')
    
    ccrecipients = self.prev_cc
    torecipients = []
    
    # Harvest email addresses from the cc, reporter, owner and status fields
    cursor = self.db.cursor()
    cursor.execute("SELECT cc,reporter,owner,status FROM ticket WHERE id=%s",
                   (tktid,))
    row = cursor.fetchone()
    if row:
        ccrecipients += row[0] and row[0].replace(',', ' ').split() or []
        self.reporter = row[1]
        self.owner = row[2]
        self.status = row[3]
        if notify_reporter:
            for S in for_reporting:
                if self.status == S:
                    torecipients.append(row[1])
        if notify_owner:
            torecipients.append(row[2])
        
    if notify_updater:
        cursor.execute("SELECT DISTINCT author,ticket FROM ticket_change "
                       "WHERE ticket=%s", (tktid,))
        for author, ticket in cursor:
            torecipients.append(author)
                
    # Suppress the updater from the recipients
    updater = None
    cursor = self.db.cursor()
    cursor.execute("SELECT author FROM ticket_change WHERE ticket=%s "
                   "ORDER BY time DESC LIMIT 1", (tktid,))
    for updater, in cursor:
        break
    else:
        cursor.execute("SELECT reporter FROM ticket WHERE id=%s", (tktid,))

    for updater, in cursor:
        break
    
    return torecipients, ccrecipients

note.TicketNotifyEmail.get_recipients = get_recipients
