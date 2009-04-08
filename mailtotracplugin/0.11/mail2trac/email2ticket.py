from mail2trac.interface import IEmailHandler
from mail2trac.utils import emailaddr2user
from trac.core import *
from trac.ticket import Ticket


class EmailToTicket(Component):
    implements(IEmailHandler)

    def match(self, message):
        return True

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

        # inset items from email
        for key, value in values.items():
            ticket.values[key] = value

        # fill in default values
        ### unused for now -- needed?
        for field in ticket.fields:
            break # XXX unused loop
            name = field['name']
            if name not in values:
                value = ticket.get_value_or_default(name)
                if value is not None:
                    ticket.values[name] = value

        # create the ticket
        ticket.insert()

        return message

    def order(self):
        return None
