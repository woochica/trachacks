# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.filters.transform import Transformer
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter


class TypeClassToTicket(Component):
    """ set css-class to type on ticket. """
    implements(ITemplateStreamFilter)

    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'ticket.html':
            return stream
        if not 'ticket' in data:
            return stream
        ticket = data['ticket'].values
        fields = self.config.getlist('ticket', 'decorate_fields')
        value = ' '.join(['%s_is_%s' % (field, ticket.get(field)) for field in fields if field in ticket]
                         + [ticket.get('type')]  # backward compatibility
                         )

        def add(name, event):
            attrs = event[1][1]
            values = attrs.get(name)
            return values and ' '.join((values, value)) or value
        return stream | Transformer('//body').attr('class', add)
