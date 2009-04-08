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

        # effectively the interface for email -> ticket
        values = { 'reporter': reporter,
                   'summary': message['subject'],
                   'description': message.get_payload(),
                   'status': 'new' }

        for key, value in values.items():
            ticket.values[key] = value

        ticket.insert()
