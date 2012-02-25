#!/usr/bin/env python
# -*- coding: utf-8 -*-

from genshi.filters.transform import Transformer
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter

class TypeClassToTicket(Component):
    """ set css-class to type on ticket. """
    implements(ITemplateStreamFilter)
   
    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'ticket.html':
            return stream
        type = 'ticket' in data and data['ticket'].values.get('type','') or ''
        def add(name, event):
            attrs = event[1][1]
            values = attrs.get(name)
            return values and ' '.join(values,type) or type
        return stream | Transformer('//body').attr('class',add)

    