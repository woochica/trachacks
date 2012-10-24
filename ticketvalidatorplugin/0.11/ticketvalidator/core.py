# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Max Stewart <max.e.stewart@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import *
from trac.ticket import ITicketManipulator
from trac.ticket import TicketSystem

class RequiredFieldValidator(Component):
    """Basic ticket validator for required fields"""
    
    implements(ITicketManipulator)
    
    def _is_empty(self, value):
        """Check if 'value' is empty.
        
        :param value: the value to check
        :type value: object"""
        
        if value is None:
            return True
        
        if len(value) == 0:
            return True
        
        return False
    
    def prepare_ticket(self, req, ticket, fields, actions):
        """Not currently called, but should be provided for future
        compatibility."""

    def validate_ticket(self, req, ticket):
        """Make sure required fields for the next state have been 
        the ticket will be in have been entered."""

        state = self._get_state(req, ticket)

        required_fields = self.config.getlist('ticketvalidator', 
                                              state + '.required')
        
        errors = [(field_name, '%s is required' % field_name) 
                  for field_name in required_fields 
                  if self._is_empty(ticket[field_name])]
        
        return errors
    
    def _get_state(self, req, ticket):
        """Get the state this ticket is going to be in."""
        
        if 'action' not in req.args:
            return 'new'
        
        action = req.args['action']
        action_changes = {}
        
        for controller in self._get_action_controllers(req, ticket, action):
            action_changes.update(controller.get_ticket_changes(req, ticket, action))
        
        return 'status' in action_changes and action_changes['status'] or ticket['status']
        
    def _get_action_controllers(self, req, ticket, action):
        
        for controller in TicketSystem(self.env).action_controllers:
            actions = [action for weight, action in
                       controller.get_ticket_actions(req, ticket)]
            if action in actions:
                yield controller

