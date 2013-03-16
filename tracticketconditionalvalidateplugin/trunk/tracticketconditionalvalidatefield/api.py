# -*- coding: utf-8 -*-
# Copyright (C) 2012 Zack Shahan <zshahan@dig-inc.net>
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.ticket.api import ITicketManipulator

import re

class TicketsValidator(Component):
    implements(ITicketManipulator)
    
    def __init__(self):
        self.defin_patt = re.compile(r'(\w+)\.(\w+)')
        self._validate_config = self._get_validate_config()

    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass
        
    def validate_ticket(self, req, ticket):
        result = None

        if ticket.values['type'] and ticket.values['type'] != '':
            if ticket.values['type'] in self._validate_config.keys():
                validator = self._validate_config[ticket.values['type']]
                for field in validator.split(','):
                    errorMessage = self._validate(req, ticket, field)
                    if errorMessage:
                        yield None, errorMessage

    def _validate(self, req, ticket, field):
        if field in self._validate_config.keys():
            field_options = self._validate_config[field]
            # get error message
            errorMessage = field_options['tip']
        
            # validate field
            rule = field_options['rule']

        fieldValue = None
        if ticket.values.has_key(field):
            fieldValue = ticket.values.get(field)
        elif req.args.has_key(field):
            fieldValue = req.args.get(field)
        
        if fieldValue is not None:
            if (not fieldValue) or (rule and re.match(rule, fieldValue) == None):
                return errorMessage

    def _get_validate_config(self):
        config = self.config['ticket_validate']
        options = {}
        for key, val in config.options():
            m = self.defin_patt.match(key)
            if m:
                prefix, attribute = m.groups()
                option = options.setdefault(prefix, {})
                option[attribute] = val
            else:
                options[key] = val     
        return options
