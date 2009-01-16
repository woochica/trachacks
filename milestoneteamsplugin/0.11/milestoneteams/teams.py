# Trac core imports
from trac.core import *
from trac.config import *

# Trac extension point imports
from trac.ticket.api import ITicketChangeListener

# Trac class imports
from trac.ticket.notification import TicketNotifyEmail
from trac.util.datefmt import utc
from trac.log import logger_factory

# Python library imports
from datetime import datetime, timedelta

class mtTicketNotification(Component):
    """Notifies teams of tickets added to their milestones."""
    implements(ITicketChangeListener)

    def ticket_created(self, ticket):
        """Notify teams when a ticket is created"""
        self.log.info("Ticket was created.")
        if (self._check_ticket(ticket)):
            self.log.info("Ticket fits criteria.")
            self._send_ticket(ticket, True)

    def ticket_changed(self, ticket, comment, author, old_values):
        """Notify teams when a ticket is changed"""
        self.log.info("Ticket was changed.")
        if (self._check_ticket(ticket, old_values)):
            self.log.info("Ticket fits criteria.")
            self._send_ticket(ticket)

    def ticket_deleted(self_ticket):
        """Not implemented for email notifications."""

    def _check_ticket(self, ticket, old_values=None):
        milestone_changed = False
        milestone_members = 0

        # First check to see if there even is a milestone
        if old_values == None:
            # This is a new ticket, check to see if the milestone is set
            if 'milestone' in ticket.values.keys():
                milestone_changed = True
        else:
            # This is a pre-existing ticket, check to see if the milestone has changed
            if 'milestone' in old_values.keys():
                milestone_changed = True
        
        # If the milestone is not set or changed, then we avoid doing the database hits
        if milestone_changed:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(milestone) FROM milestone_teams WHERE milestone=%s AND notify > %s", (ticket.values['milestone'], 0))
            try:
                milestone_members = int(cursor.fetchone()[0])
            except:
                milestone_members = 0
            db.close()
  
            self.log.debug("Check Ticket: %s" % (milestone_changed and milestone_members > 0))
            return (milestone_members > 0)
        else:
            self.log.debug("Check Ticket: Milestone didn't change.")
            return (milestone_changed)

    def _send_ticket(self, ticket, newticket=False):
        """Send email to Milestone informatives"""

        torcpts = []
        ccrcpts = []

        # We need to get the team members from the database.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT username, role FROM milestone_teams WHERE milestone=%s AND notify > 0", (ticket.values['milestone'], ))
        for row in cursor:
            if int(row[1]) > 0:
                torcpts.append(row[0])
            else:
                ccrcpts.append(row[0])
        
        tn=mtNotifyEmail(self.env)
        tn.set_recipients(torcpts, ccrcpts)
        tn.notify(ticket, newticket, datetime.now(utc))

class mtNotifyEmail(TicketNotifyEmail):
    """Sends ticket emails when milestones are modified"""
    
    team_torcpts = None
    team_ccrcpts = None

    def __init__(self, env):
        TicketNotifyEmail.__init__(self, env)
        self.team_torcpts = []
        self.team_ccrcpts = []
        
    def set_recipients(self, torcpts=None, ccrcpts=None):
        if isinstance(torcpts, list) and torcpts:
            self.team_torcpts = torcpts
        if isinstance(ccrcpts, list) and ccrcpts:
            self.team_ccrcpts = ccrcpts

    def get_recipients(self, tktid):
        (torcpts, ccrcpts) = TicketNotifyEmail.get_recipients(self, tktid)
        newtolist = []
        newcclist = []

        for notify in self.team_torcpts:
            if notify not in torcpts and notify not in ccrcpts:
                newtolist.append(notify)
        for notify in self.team_ccrcpts:
            if notify not in torcpts and notify not in ccrcpts:
                newcclist.append(notify)

        self.env.log.debug("Default To: %s" % (torcpts))
        self.env.log.debug("Changed To: %s" % (newtolist))
        self.env.log.debug("Default CC: %s" % (ccrcpts))
        self.env.log.debug("Changed CC: %s" % (newcclist))

        return (newtolist, newcclist)
