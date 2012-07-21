# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 ERCIM
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Authors: Jean-Guilhem Rouel <jean-guilhem.rouel@ercim.org>
#          Vivien Lacourba <vivien.lacourba@ercim.org>

from trac.core import *
from trac.ticket.api import ITicketManipulator

from defaultcc.model import DefaultCC

class TicketDefaultCC(Component):
    """Automatically adds a default CC list when new tickets are created.
    
    Tickets are modified right after their creation to add the component's 
    default CC list to the ticket CC list.
    """

    implements(ITicketManipulator)

    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        comp_default_cc = DefaultCC(self.env, ticket['component'])
        if comp_default_cc and comp_default_cc.cc:
            if ticket['cc']:
                ticket['cc'] += ', '
            ticket['cc'] += comp_default_cc.cc

        return []
