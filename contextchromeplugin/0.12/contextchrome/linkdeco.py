#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.web.api import IRequestHandler
from trac.config import ListOption
from trac.util import Ranges

class TicketLinkDecorator(Component):
    """ set css-class to ticket link as ticket field value. field name can set in [ticket]-decorate_fields in trac.ini"""
    implements(IRequestHandler)

    wrapped = None
    
    decorate_fields = ListOption('ticket','decorate_fields',
                        doc=
                        """ comma separated List of field names to add css class of ticket link.
                            (Provided by !ContextChrome.!TicketLinkDecorator) """)

    def __init__(self):
        Component.__init__(self)
        if not self.wrapped: self.wrap()
  
    def wrap(self):
        ticketsystem = self.compmgr[TicketSystem]
        def _format_link(*args, **kwargs): # hook method
            element = self.wrapped(*args, **kwargs)
            class_ = element.attrib.get('class')
            if class_ and element.attrib.get('href'): # existing ticket
                deco = self.get_deco(*args, **kwargs) or []
                element.attrib = element.attrib | [('class', ' '.join(deco + [class_]))]
            return element
        self.wrapped = ticketsystem._format_link
        ticketsystem._format_link = _format_link

    def get_deco(self, formatter, ns, target, label, fullmatch=None):
        link, params, fragment = formatter.split_link(target)
        r = Ranges(link)
        if len(r) == 1:
            num = r.a
            ticket = formatter.resource('ticket', num)
            from trac.ticket.model import Ticket
            if Ticket.id_is_valid(num) and \
                    'TICKET_VIEW' in formatter.perm(ticket):
                ticket = Ticket(self.env, num)
                decorate_fields = self.config.getlist('ticket','decorate_fields')
                return [x for x in [ticket.get_value_or_default(field) for field in decorate_fields] if x is not None]

    # IRequestHandler Methods
    def match_request(self, req):
        return False
        
    def process_request(self, req):
        pass