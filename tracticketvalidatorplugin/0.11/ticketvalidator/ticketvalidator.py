# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         ticketvalidator.py
# Purpose:      The ticket validator Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------
from trac.config import BoolOption, IntOption, ListOption

from trac.core import *
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.util.html import html, Markup

import re

class TicketsValidator(Component):
    """ Validate ticket fields.
        Only authenticated user or anonymous with valid email address can submit.
    """
    
    implements(ITicketManipulator)

    validate_author = BoolOption('ticketvalidator', 'validate_author', 'false', '')
    validates = ListOption('ticketvalidator', 'validates', [])

    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass
        
    def validate_ticket(self, req, ticket):
        result = None

        if self.validate_author:
            errorMessage = self._validateAuthor(req, ticket)
            if errorMessage:
                yield None, errorMessage

        for field in self.validates:
            errorMessage = self._validateField(req, ticket, field)
            if errorMessage:
                yield None, errorMessage


    # private methods
    def _validateAuthor(self, req, ticket):
        # get error message
        errorMessage = self.config.get('ticketvalidator', 'validate_author.tip', "Ticket field is not filled correctly.")

        # is logged in?
        if req.authname == 'anonymous':
            isLoggedIn = False
        else:
           isLoggedIn = True
           
        # get author
        author = req.args.get("author")
        reporter = ticket.values.get("reporter")
        
        # validate author
        if not isLoggedIn:
            if ticket.exists:
                if not self._isValidateEmail(author):
                    return errorMessage
            else:
                if not self._isValidateEmail(author) and not self._isValidateEmail(reporter):
                    return errorMessage

    def _validateField(self, req, ticket, field):
        # get error message
        errorMessage = self.config.get('ticketvalidator', '%s.tip' % field, "Ticket field is not filled correctly.")
        
        # validate field
        rule = self.config.get('ticketvalidator', '%s.rule' % field, None)

        fieldValue = None
        if ticket.values.has_key(field):
            fieldValue = ticket.values.get(field)
        elif req.args.has_key(field):
            fieldValue = req.args.get(field)
        
        if fieldValue is not None:
            if (not fieldValue) or (rule and re.match(rule, fieldValue) == None):
                return errorMessage
                
    def _isValidateEmail(self, email):
        if not email:
            return False

        if len(email) > 7:
            if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+\.[a-zA-Z]{2,6}$", email) != None:
                return True
        return False

