from trac.config import *
from trac.ticket.notification import TicketNotifyEmail

class SpecialTicketNotifyEmail(TicketNotifyEmail):
    """Special Notification of ticket changes."""
    __team = None
    
    def notify(self, ticket, newticket=True, modtime=None):
        self.__team = ticket["ttd"]
        if self.__team != None:
            TicketNotifyEmail.notify(self, ticket, newticket, modtime)
        else:
            self.env.log.warning("Ticket has no custom field called 'ttd'!")
    
    def parse_recipient(self):
        count = self.env.config.getint('ticket-team-dispatcher', 'count', 0)
        for i in xrange(count): 
            if self.__team == self.config.get('ticket-team-dispatcher', '%i.team' % i, None):
                return self.config.get('ticket-team-dispatcher', '%i.dispatcher' % i, None)
        return None

    def get_recipients(self, tktid):
        return ([self.parse_recipient()], [])
