'''
Custom Wiki Macros for use in the application

    @author: scott turnbull <sturnbu@emory.edu>
    Copyright (C) 2010  Scott Turnbull

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.wiki.api import parse_args
from trac.ticket.query import Query
from trac.util.text import shorten_line
from trac.web.chrome import add_stylesheet, Chrome

from genshi.builder import tag


class SpTicketQueryMacro(WikiMacroBase):
    """
    Reworking of the TicketQuery macro to add functionality.  Some lines are
    taken directly from that code.
    
    addition functions:
    
    List returns will add additional fields specified in the standard 'col' 
    keyword as annotations to the end of the summary.
    
    'total' format returns total SP for all matching tickets.
    'completed' format returns total SP for all completed tickets.
    'remaining' format returns total SP for all unclosed tickets.
    'storypoints' format returns a text formatted summary of storypoint status.
    
    *** Original Comments read as follows ***
    
    Macro that lists tickets that match certain criteria.
    
    This macro accepts a comma-separated list of keyed parameters,
    in the form "key=value".

    If the key is the name of a field, the value must use the syntax 
    of a filter specifier as defined in TracQuery#QueryLanguage.
    Note that this is ''not'' the same as the simplified URL syntax 
    used for `query:` links starting with a `?` character.

    In addition to filters, several other named parameters can be used
    to control how the results are presented. All of them are optional.

    The `format` parameter determines how the list of tickets is
    presented: 
     - '''list''' -- the default presentation is to list the ticket ID next
       to the summary, with each ticket on a separate line.
     - '''compact''' -- the tickets are presented as a comma-separated
       list of ticket IDs. 
     - '''count''' -- only the count of matching tickets is displayed
     - '''table'''  -- a view similar to the custom query view (but without
       the controls)

    The `max` parameter can be used to limit the number of tickets shown
    (defaults to '''0''', i.e. no maximum).

    The `order` parameter sets the field used for ordering tickets
    (defaults to '''id''').

    The `group` parameter sets the field used for grouping tickets
    (defaults to not being set).

    The `groupdesc` parameter indicates whether the natural display
    order of the groups should be reversed (defaults to '''false''').

    The `verbose` parameter can be set to a true value in order to
    get the description for the listed tickets. For '''table''' format only.
    ''deprecated in favor of the `rows` parameter''
    
    The `rows` parameter can be used to specify which field(s) should 
    be viewed as a row, e.g. `rows=description|summary`

    For compatibility with Trac 0.10, if there's a second positional parameter
    given to the macro, it will be used to specify the `format`.
    Also, using "&" as a field separator still works but is deprecated.
    """
    
    def expand_macro(self, formatter, name, content):
        
        argv, kwargs = parse_args(content, strict=False) # parse args and kwargs
        
        # Grab the format needed.
        if len(argv) > 0 and not 'format' in kwargs: # 0.10 compatibility hack
            kwargs['format'] = argv[0]
        fmt = kwargs.pop('format', 'list').strip().lower() # Get the requested fmt type
        
        kwargs['col'] = self._check_cols(kwargs.get('col', ''), fmt) # define the kwargs and set some defaults
        
        # Build the ticket query and retrieve the tickets.
        query_string = self._get_querystring(kwargs) # Construct the querystring.
        query = self._get_query(query_string) # Get the Query Object.
        tickets = self._get_tickets(query, formatter.req) # Get the tickets
        
        if not tickets: # If no tickets are returned
            return tag.span(("No results"), class_='query_no_results')
        
        # 'table' format had its own permission checks, here we need to
        # do it explicitly:
        if fmt != 'table':
            tickets = [t for t in tickets if 'TICKET_VIEW' in formatter.req.perm('ticket', t['id'])]
        
        # Return based on format requested.
        switch = {
                  'count': self._count_tickets(tickets),
                  'total': self._sp_total(tickets),
                  'completed': self._sp_completed(tickets),
                  'remaining': self._sp_remaining(tickets),
                  'storypoints': self._display_storypoints(tickets),
                  'list': self._display_list(tickets, kwargs['col'], formatter.req),
                  'compact': self._display_compact_list(tickets, formatter.req),
                  'table': self._display_table(tickets, formatter, query)
                  }
        
        try: # little fall back if they select an unsupported format
            output = switch[fmt]
        except KeyError:
            output = tag.span(("Invalid output format: '%s'" % fmt), class_='error')
    
        return output
    
    def _display_list(self, tickets, cols, req):
        '''Returns a list formatted '''
        return tag.div(tag.dl([(tag.dt(self._format_ticket_link(ticket, req)),
                                tag.dd(self._format_ticket_label(ticket, cols)))
                               for ticket in tickets],
                              class_='wiki compact'))
    
    def _display_compact_list(self, tickets, req):
        '''Displays a compact list'''
        alist = [self._format_ticket_link(ticket, req) for ticket in tickets]
        if len(alist) > 0:
            return tag.span(alist[0], *[(', ', a) for a in alist[1:]])
        else:
            return "No Tickets found that match query."
    
    def _display_table(self, tickets, formatter, query):
        '''Displays table view of tickets'''
        data = query.template_data(formatter.context, tickets)
        add_stylesheet(formatter.req, 'common/css/report.css')
        
        return Chrome(self.env).render_template(formatter.req, 'query_results.html', data, None, fragment=True)
    
    def _display_storypoints(self, tickets):
        '''Returns some text summarizing story point totals'''
        details = (self._sp_total(tickets), self._sp_completed(tickets), self._sp_remaining(tickets))
        return "%s Total Story Points with %s Completed and %s Remaining." % details
    
    def _format_ticket_link(self, ticket, req):
        return tag.a('#%s' % ticket['id'],
                         class_=ticket['status'],
                         href=req.href.ticket(int(ticket['id'])),
                         title=shorten_line(ticket['summary']))
    
    def _format_ticket_label(self, ticket, cols):
        '''Returns a sting of the ticket summary and any additional columns as annotations to the end.'''
        skip = ['id', 'status', 'summary'] # Exclude these cols from label
        fields = cols.split('|') 
        for item in skip: # Remove skipped items from the fields list.
            if item in fields:
                fields.remove(item)
        if fields > 0:
            notes = "; ".join("%s: %s" % (field, ticket[field]) for field in fields if field in ticket.keys())
            output = "%s [%s]" % (ticket['summary'], notes)
        else:
            output = ticket['summary']
        return output
    
    def _check_cols(self, cols, fmt=''):
        '''Formats column arguments to include default values'''
        defaults = ['summary', 'status'] # add any default columns here.
        if fmt in ['storypoints', 'total', 'completed', 'remaining']:
            defaults.append('storypoints') # This needs included for tally formats to work.
        fields = cols.split("|")
        for field in defaults:
            if field in fields:
                defaults.remove(field)
        final = defaults + fields
        return "|".join(final)
    
    def _get_querystring(self, kwargs):
        return '&'.join(['%s=%s' % item for item in kwargs.iteritems()])
    
    def _get_query(self, query_string):
        '''Returns the query object from a query string.'''
        return Query.from_string(self.env, query_string)
    
    def _get_tickets(self, query, req):
        '''Returns a list of ticket objects.'''
        rawtickets = query.execute(req) # Get all tickets
        # Do permissions check on tickets
        tickets = [t for t in rawtickets 
                   if 'TICKET_VIEW' in req.perm('ticket', t['id'])]
        return tickets
        
    def _count_tickets(self, tickets):
        '''Counts matches on a query.'''
        return len(tickets)
        
    def _sp_total(self, tickets):
        '''Returns total SP for all the tickets.'''
        total = 0.0
        for ticket in tickets:
            try:
                total += float(ticket['storypoints'])
            except (KeyError, ValueError):
                continue # Just keep doin' your thing man.
        return total
        
    def _sp_completed(self, tickets):
        '''Returns total SP for all completed tickets.'''
        # Grab all closed tickets
        t = [ticket for ticket in tickets if ticket['status'] == 'closed']
        return self._sp_total(t)
        
    def _sp_remaining(self, tickets):
        '''Returns total SP of all tickets not completed'''
        # Grab all open tickets
        t = [ticket for ticket in tickets if ticket['status'] != 'closed']
        return self._sp_total(t)