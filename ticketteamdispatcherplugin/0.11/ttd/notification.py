from trac.config import *
from trac.ticket.notification import TicketNotifyEmail

from tracusermanager.api import UserManager, User

class SpecialTicketNotifyEmail(TicketNotifyEmail):
    """Special Notification of ticket changes."""
    __team = None
    
    def notify(self, ticket, newticket=True, modtime=None):
        self.__team = ticket["ttd"]
        if self.__team != None:
            TicketNotifyEmail.notify(self, ticket, newticket, modtime)
        else:
            self.env.log.warning("Ticket has no custom field called 'ttd'!")
    
    def get_recipients(self, tktid):
        recipients = []
        #self.env.log.warning('Sending to %s' % self.__team)
        for user in UserManager(self.env).get_active_users():
            if user[self.__team] == '1':
                recipients.append(user['email'])
                #self.env.log.warning('Whhich is %s %s.' % (user.username, user['email']))
        return (recipients, [])
