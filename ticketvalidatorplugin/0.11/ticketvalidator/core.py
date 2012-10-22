# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Max Stewart
# All rights reserved.
#
# This file is part of the TicketValidator plugin for Trac
#
# TicketValidator is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as 
# published by the Free Software Foundation, either version 3 of 
# the License, or (at your option) any later version.
#
# TicketValidator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TicketValidator.  If not, see 
# <http://www.gnu.org/licenses/>.

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

