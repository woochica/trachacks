# -*- coding: utf-8 -*-
# Copyright (C) 2010, 2012 Steffen Hoffmann <hoff.st@shaas.net>
#

from trac.config        import Option
from trac.ticket.query  import Query
from trac.util.text     import to_unicode
from trac.wiki.api      import parse_args

from wikicalendar.api   import WikiCalendarBuilder


__all__ = ['WikiCalendarTicketProvider']


class WikiCalendarTicketProvider(WikiCalendarBuilder):
    """Custom TicketQuery macro implementation for WikiTicketCalendarMacro.

    Most lines were taken directly from that code.
    *** Original Comments as follows (shortend)***
    Macro that lists tickets that match certain criteria.

    This macro accepts a comma-separated list of keyed parameters,
    in the form "key=value".

    If the key is the name of a field, the value must use the syntax
    of a filter specifier as defined in TracQuery#QueryLanguage.
    Note that this is ''not'' the same as the simplified URL syntax
    used for `query:` links starting with a `?` character.

    In addition to filters, several other named parameters can be used
    to control how the results are presented. All of them are optional.

    Also, using "&" as a field separator still works but is deprecated.
    """

    def declare(self):
        return {
            'capability': ['harvest'],
            'resource': 'ticket',
            'target': 'body',
        }

    def harvest(self, req, content):
        """TicketQuery provider method."""
        due_field_name = self.config.get('wikiticketcalendar',
                                         'ticket.due_field.name')

        # Parse args and kwargs.
        argv, kwargs = parse_args(content, strict=False)

        # Define minimal set of values.
        std_fields = ['description', 'owner', 'status', 'summary']
        kwargs['col'] = "|".join(std_fields + [due_field_name])

        # Construct the querystring.
        query_string = '&'.join(['%s=%s' %
            item for item in kwargs.iteritems()])

        # Get the Query Object.
        query = Query.from_string(self.env, query_string)

        # Get the tickets.
        tickets = self._get_tickets(query, req)
        return tickets

    def _get_tickets(self, query, req):
        '''Returns a list of ticket objects.'''
        rawtickets = query.execute(req) # Get all tickets
        # Do permissions check on tickets
        tickets = [t for t in rawtickets
                   if 'TICKET_VIEW' in req.perm('ticket', t['id'])]
        return tickets
