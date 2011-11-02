"""
Trac email handlers having to do with tickets
"""

import os
import re

from mail2trac.email2trac import EmailException
from mail2trac.interface import IEmailHandler
from mail2trac.utils import add_attachments
from mail2trac.utils import emailaddr2user
from mail2trac.utils import get_description_and_attachments
from mail2trac.utils import strip_res
from trac.core import *
from trac.mimeview.api import KNOWN_MIME_TYPES
from trac.config import Option
from trac.perm import PermissionSystem
from trac.ticket import Ticket
from trac.ticket.notification import TicketNotifyEmail


### email handlers

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
        description, attachments = get_description_and_attachments(message)
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

        # add attachments to the ticket
        add_attachments(self.env, ticket, attachments)

        # do whatever post-processing is necessary
        self.post_process(ticket)

        # add local warnings
        if _warnings:
            warning = """A ticket has been created but there is a problem:\n\n%s\n\nPlease edit your ticket by going here: %s""" % ('\n\n'.join([' - %s' % warning for warning in _warnings]), self.env.abs_href('ticket', ticket.id))
            warnings.append(warning)

    ### internal methods

    def reporter(self, message):
        """return the ticket reporter or updater"""
        user = emailaddr2user(self.env, message['from'])
        
        # check permissions
        perm = PermissionSystem(self.env)
        if not perm.check_permission('TICKET_CREATE', user): # None -> 'anoymous'
            raise EmailException("%s does not have TICKET_CREATE permissions" % (user or 'anonymous'))
    
        reporter = user or message['from']
        return reporter

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


class ReplyToTicket(Component):
    
    implements(IEmailHandler)

    def match(self, message):
        return bool(self.ticket(message))

    def invoke(self, message, warnings):
        """reply to a ticket"""
        ticket = self.ticket(message)
        reporter = self.reporter(message)

        # get the description and attachments
        description, attachments = get_description_and_attachments(message)
        if not description:
            warnings.append("Seems to be a reply to %s but I couldn't find a comment")
            return message
        
        # save changes to the ticket
        ticket.save_changes(reporter, description)

        # ticket notification
        tn = TicketNotifyEmail(self.env)
        tn.notify(ticket, newticket=0, modtime=ticket.time_changed)


    ### internal methods

    def ticket(self, message):
        """
        return a ticket associated with a message subject,
        or None if not available
        """

        # get and format the subject template
        subject_template = self.env.config.get('notification', 'ticket_subject_template')
        prefix = self.env.config.get('notification', 'smtp_subject_prefix')
        subject_template = subject_template.replace('$prefix', prefix).replace('$summary', 'summary').replace('$ticket.id', 'ticketid')
        subject_template_escaped = re.escape(subject_template)

        # build the regex
        subject_re = subject_template_escaped.replace('summary', '.*').replace('ticketid', '([0-9]+)')

        # get the real subject
        subject = strip_res(message['subject'])
        
        # see if it matches the regex
        match = re.match(subject_re, subject)
        if not match:
            return None

        # get the ticket
        ticket_id = int(match.groups()[0])
        try:
            ticket = Ticket(self.env, ticket_id)
        except:
            return None

        return ticket

    def reporter(self, message):
        """return the ticket updater"""
        user = emailaddr2user(self.env, message['from'])

        # check permissions
        perm = PermissionSystem(self.env)
        if not perm.check_permission('TICKET_APPEND', user): # None -> 'anoymous'
            raise EmailException("%s does not have TICKET_APPEND permissions" % (user or 'anonymous'))
    
        reporter = user or message['from']
        return reporter

