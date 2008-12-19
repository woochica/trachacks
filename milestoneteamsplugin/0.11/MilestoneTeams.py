from datetime import datetime, timedelta
from trac.core import *
from trac.config import *
from trac.ticket.api import ITicketChangeListener
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.model import Ticket
from trac.util.datefmt import utc
from trac.log import logger_factory

class MilestoneTeamSetupParticipant(Component):
    """Sets up Trac system for the Milestone Teams plugin."""
    pass

class MilestoneTeamConfiguration(Component):
    """Modifies Trac UI for editing Milestone Teams"""
    pass

class MilestoneTeamTicketNotification(Component):
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
        milestone_reactor = False

        if old_values == None:
            if 'milestone' in ticket.values.keys():
                milestone_changed = True
        else:
            if 'milestone' in old_values.keys():
                milestone_changed = True

        if ticket.values['milestone'][0:8] == 'Reactor-':
            milestone_reactor = True

        self.log.debug("Check Ticket: %s" % (milestone_changed and milestone_reactor))
        return (milestone_changed and milestone_reactor)

    def _send_ticket(self, ticket, newticket=False):
        """Send email to Milestone informatives"""
        tn=MilestoneTicketNotifyEmail(self.env)
        tn.notify(ticket, newticket, datetime.now(utc))

class MilestoneTicketNotifyEmail(TicketNotifyEmail):
    """Sends ticket emails when milestones are modified"""

    def __init__(self, env):
        TicketNotifyEmail.__init__(self, env)

    def get_recipients(self, tktid):
        (torcpts, ccrcpts) = TicketNotifyEmail.get_recipients(self, tktid)
        newcclist = [u'silvein',]

# This is commented out so that I can get the emails for testing even though I am the reporter/owner
#        for notify in notifiers:
#            if notify not in torcpts and notify not in ccrcpts:
#                newcclist.append(notify)

        self.env.log.debug("Default To: %s" % (torcpts))
        self.env.log.debug("Default CC: %s" % (ccrcpts))
        self.env.log.debug("Changed CC: %s " % (newcclist))

        return (newcclist, [])















