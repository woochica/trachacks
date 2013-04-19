# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from componentdependencies.interface import IRequireComponents
from hours import TracHoursPlugin
from trac.core import * 
from trac.perm import PermissionCache
from trac.ticket.api import ITicketManipulator
from trac.ticket.api import ITicketChangeListener

try:
    from mail2trac.interface import IEmailHandler
    from mail2trac.email2ticket import ReplyToTicket
    from mail2trac.utils import emailaddr2user
except ImportError:
    IEmailHandler = None

class TracHoursByComment(Component):

    if IEmailHandler:
        implements(IEmailHandler, IRequireComponents, ITicketManipulator, ITicketChangeListener)
    else:
        implements(IRequireComponents, ITicketManipulator, ITicketChangeListener)

    # for ticket comments: 1.5 hours or 1:30 hours
    hours_regex = '(([0-9]+(\.[0-9]+)?)|([0-9]+:[0-5][0-9])) *hours'

    # for singular hours: 1 hour
    singular_hour_regex = r'((^)|(\s))1 *hour((\W)|($))' 

    ### method for IRequireComponents
    def requires(self):
        return [TracHoursPlugin]

    ### methods for ITicketManipulator
    
    def prepare_ticket(self, req, ticket, fields, actions):
        """Not currently called, but should be provided for future
        compatibility."""

    def validate_ticket(self, req, ticket):
        """add hours through comments"""

        if not req.perm.has_permission('TICKET_ADD_HOURS'):
            return []

        # markup the comment and add hours
        comment = req.args.get('comment')
        if comment is None:
            return []

        req.args['comment'] = self.munge_comment(comment, ticket)
        return []

    def munge_comment(self, comment, ticket):
        def replace(match, ticket=ticket):
            """
            callback for re.sub; this will markup the hours link
            """
            return u'[%s %s]' % (('/hours/%s' % ticket.id), match.group())

        comment = re.sub(self.hours_regex, replace, comment)
        comment = re.sub(self.singular_hour_regex, u' [/hours/%s 1 hour]' % ticket.id, comment)
        return comment

    ### methods for IEmailHandler

    def match(self, message):
        reporter = emailaddr2user(self.env, message['from'])
        reply_to_ticket = ReplyToTicket(self.env)
        
        perm = PermissionCache(self.env, reporter)        
        if not perm.has_permission('TICKET_ADD_HOURS'):
            return False
        return bool(reply_to_ticket.ticket(message))

    def invoke(self, message, warnings):
        reply_to_ticket = ReplyToTicket(self.env)
        ticket = reply_to_ticket.ticket(message)
        payload = message.get_payload()
        if isinstance(payload, basestring):
            if message.get('Content-Disposition', 'inline') == 'inline' and message.get_content_maintype() == 'text':
                message.set_payload(self.munge_comment(payload, ticket))
        else:
            for _message in payload:
                self.invoke(_message, warnings)
        return message


    ### methods for ITicketChangeListener

    """Extension point interface for components that require notification
    when tickets are created, modified, or deleted."""

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.
        
        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        perm = PermissionCache(self.env, author)
        if perm.has_permission('TICKET_ADD_HOURS'):
            self.add_hours_by_comment(comment, ticket.id, author)

    def ticket_created(self, ticket):
        """Called when a ticket is created."""

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        # TODO: delete hours for this ticket

    ### internal method
    def add_hours_by_comment(self, comment, ticket, worker):
        """
        add hours to a ticket via a comment string
        * comment : the comment string
        * ticket : the id of the ticket
        * worker : who worked the hours
        """
        trachours = TracHoursPlugin(self.env)
        for match in re.finditer(self.hours_regex, comment):
            hours = match.groups()[0]
            if ':' in hours:
                hours, minutes = hours.split(':')
                seconds = 3600.0*float(hours) + 60.0*float(minutes)
            else:
                seconds = 3600.0*float(hours)
            _comment = re.sub('\[/hours/[0-9]+ ' + self.hours_regex + '\]', match.group(), comment)
            trachours.add_ticket_hours(ticket, worker, seconds, comments=_comment)

        for match in re.finditer(self.singular_hour_regex, comment):
            _comment = re.sub('\[/hours/[0-9]+ 1 hour\]', '1 hour', comment)
            trachours.add_ticket_hours(ticket, worker, 3600.0, comments=_comment)

