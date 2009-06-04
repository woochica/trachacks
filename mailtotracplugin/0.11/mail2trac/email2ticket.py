import base64
import os

from mail2trac.email2trac import EmailException
from mail2trac.interface import IEmailHandler
from mail2trac.utils import emailaddr2user
from trac.attachment import Attachment
from trac.core import *
from trac.mimeview.api import KNOWN_MIME_TYPES
from trac.perm import PermissionSystem
from trac.ticket import Ticket
from trac.ticket.notification import TicketNotifyEmail
from StringIO import StringIO

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

        description, attachments = self.get_description_and_attachments(message)
        if description is None:
            description = ''
        description = description.strip()

        fields = self.fields(message, reporter=reporter, description=description)

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

        ctr = 1
        # add attachments to the ticket
        for msg in attachments:
            attachment = Attachment(self.env, 'ticket', ticket.id)
            attachment.author = ticket['reporter']
            attachment.description = ticket['summary']
            payload = msg.get_payload()
            if msg.get('Content-Transfer-Encoding') == 'base64':
                payload = base64.b64decode(payload)
            size = len(payload)
            filename = msg.get_filename() or message.get('Subject')
            if not filename:
                filename = 'attachment-%d' % ctr
                extensions = KNOWN_MIME_TYPES.get(message.get_content_type())
                if extensions:
                    filename += '.%s' % extensions[0]
                ctr += 1
            buffer = StringIO()
            print >> buffer, payload
            buffer.seek(0)
            attachment.insert(filename, buffer, size)
            os.chmod(attachment._get_path(), 0666)
            # TODO : should probably chown too

        # ticket notification
        tn = TicketNotifyEmail(self.env)
        tn.notify(ticket)

    def order(self):
        return None


    ### internal methods

    def get_description_and_attachments(self, message, description=None, attachments=None):
        if attachments is None:
            attachments = []
        payload = message.get_payload()
        if isinstance(payload, basestring):

            # XXX could instead use .is_multipart
            if description is None and message.get('Content-Disposition', 'inline') == 'inline' and message.get_content_maintype() == 'text': 

                description = payload.strip()
                if message.get_content_subtype() == 'html':
                    # markup html email
                    description = '{{{\n#!html\n' + description + '}}}'
            else:
                if payload.strip() != description:
                    attachments.append(message)
        else:
            for _message in payload:
                description, _attachments = self.get_description_and_attachments(_message, description, attachments)

        return description, attachments


    def fields(self, message, **fields):

        # effectively the interface for email -> ticket
        fields.update(dict(summary=message['subject'],
                           status='new',
                           resolution=''))
        return fields
