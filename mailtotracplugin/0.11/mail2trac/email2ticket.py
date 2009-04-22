from mail2trac.email2trac import EmailException
from mail2trac.interface import IEmailHandler
from mail2trac.utils import emailaddr2user
from trac.core import *
from trac.perm import PermissionSystem
from trac.ticket import Ticket


class EmailToTicket(Component):
    """create a ticket from an email"""

    implements(IEmailHandler)

    ### methods for IEmailHandler

    def match(self, message):
        return True

    def invoke(self, message):
        """make a new ticket on receiving email"""


        user = emailaddr2user(self.env, message['from'])
        
        # check permissions
        perm = self.env[PermissionSystem]
        if not perm.check_permission('TICKET_CREATE', user): # None -> 'anoymous'
            raise EmailException("%s does not have TICKET_CREATE permissions" % (user or 'anonymous'))


        ticket = Ticket(self.env)
        reporter = user or message['from']

        fields = self.fields(message, reporter=reporter)

        # inset items from email
        for key, value in fields.items():
            ticket.values[key] = value

        # fill in default values
        ### unused for now -- needed?
        for field in ticket.fields:
            name = field['name']
            if name not in fields:
                value = ticket.get_value_or_default(name) or ''
                if value is not None:
                    ticket.values[name] = value

        # create the ticket
        ticket.insert()

    def order(self):
        return None


    ### internal methods

    def fields(self, message, **fields):

        # effectively the interface for email -> ticket
        fields.update(dict(summary=message['subject'],
                           description=message.get_payload(),
                           status='new'))
        return fields
