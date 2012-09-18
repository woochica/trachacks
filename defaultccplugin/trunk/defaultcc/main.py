# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jean-Guilhem Rouel <jean-guilhem.rouel@ercim.org>
# Copyright (C) 2009 Vivien Lacourba <vivien.lacourba@ercim.org>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import *
from trac.ticket.api import ITicketManipulator

from defaultcc.model import DefaultCC

class TicketDefaultCC(Component):
    """Automatically adds a default CC list when new tickets are created.
    
    Tickets are modified at the time of creation by adding the component's 
    default CC list to the ticket's CC list.
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
