from mail2trac.interface import IEmailHandler
from mail2trac.utils import emailaddr2user
from trac.core import *
from trac.ticket import Ticket


class EmailToTicket(Component):
    implements(IEmailHandler)

    def invoke(self, message):
        """make a new ticket on receiving email"""


        user = emailaddr2user(self.env, message['from'])
        
        # TODO : check permissions

        ticket = Ticket(self.env)
        reporter = user or message['from']

        ticket.values['reporter'] = reporter
        ticket.values['summary'] = message['subject']
        ticket.values['description'] = message.get_payload()

        ticket.insert()
