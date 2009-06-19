import base64
import os

from mail2trac.email2trac import EmailException
from mail2trac.interface import IEmailHandler
from mail2trac.utils import emailaddr2user
from trac.attachment import Attachment
from trac.core import *
from trac.mimeview.api import KNOWN_MIME_TYPES
from trac.config import Option
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

    def invoke(self, message, warnings):
        """make a new ticket on receiving email"""

        # local warnings
        _warnings = []

        # get the ticket reporter
        reporter = self.reporter(message)

        # get the description and attachments
        description, attachments = self.get_description_and_attachments(message)
        if description is None:
            description = ''
        description = description.strip()

        # get the ticket fields
        fields = self.fields(message, _warnings, reporter=reporter, description=description)

        # inset items from email
        ticket = Ticket(self.env)
        for key, value in fields.items():
            ticket.values[key] = value

        # fill in default values
        for field in ticket.fields:
            name = field['name']
            if name not in fields:
                option = 'ticket_field.%s' % name
                if self.env.config.has_option('mail', option):
                    ticket.values[name] = self.env.config.get('mail', option)
                else:
                    try:
                        value = ticket.get_value_or_default(name) or ''
                    except AttributeError: # BBB
                        value = ''
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

        # do whatever post-processing is necessary
        self.post_process(ticket)

        # add local warnings
        if _warnings:
            warning = """A ticket has been created but there is a problem:\n\n%s\n\nPlease edit your ticket by going here: %s""" % ('\n\n'.join([' - %s' % warning for warning in _warnings]), self.env.abs_href('ticket', ticket.id))
            warnings.append(warning)

    def order(self):
        return None

    ### internal methods

    def reporter(self, message):
        """return the ticket reporter"""
        user = emailaddr2user(self.env, message['from'])
        
        # check permissions
        perm = self.env[PermissionSystem]
        if not perm.check_permission('TICKET_CREATE', user): # None -> 'anoymous'
            raise EmailException("%s does not have TICKET_CREATE permissions" % (user or 'anonymous'))

        reporter = user or message['from']
        return reporter


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


    def fields(self, message, warnings, **fields):

        # effectively the interface for email -> ticket
        fields.update(dict(summary=message['subject'],
                           status='new',
                           resolution=''))
        return fields

    def post_process(self, ticket):
        """actions to perform after the ticket is created"""

        # ticket notification
        tn = TicketNotifyEmail(self.env)
        tn.notify(ticket)
    

class ContactEmailToTicket(EmailToTicket):
    """
    form of email to ticket to allow reporting as the inquiry handler user.
    specifically, useful for contact-type tickets
    """

    trac_address = Option('mail', 'address',
                          doc="email address to listen to")

    def reporter(self, message):
        trac_address = self.trac_address
        if not trac_address:
            trac_address = self.env.config.get('notification', 'smtp_replyto')
        user = emailaddr2user(self.env, trac_address)
        if user:
            return user
        return trac_address

    def fields(self, message, warnings, **fields):
        fields = EmailToTicket.fields(self, message, warnings, **fields)
        if message['from']:
            fields['summary'] = 'From %s: %s' % ( message['from'], fields['summary'])
        return fields

    def post_process(self, ticket):
        """
        don't send notification emails as they wil result in a feedback loop
        """
