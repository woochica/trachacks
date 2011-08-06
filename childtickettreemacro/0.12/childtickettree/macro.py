# ChildTickets plugin

import re

# from trac.core import *
from genshi.builder import tag
from trac.core import TracError
from trac.wiki.api import parse_args
from trac.ticket.model import Ticket
from trac.util import as_bool
from trac.util.text import shorten_line
from trac.wiki.macros import WikiMacroBase

from trac.wiki.model import WikiPage

class ChildTicketTreeMacro(WikiMacroBase):
    """This macro provides a complete hierarchy of all childtickets under the given ticket.

    Examples:
    {{{
    [[ChildTicketTree]] - Used alone in a ticket field, will take the current ticket as the top level and print the tree.
    [[ChildTicketTree(#1)]] - Can be used in any wiki page anywhere and provides a tree for ticket with id '#1' ('1' ie. without '#' also accepted).
    [[ChildTicketTree(ticket=1)]] - The ticket number can also be explicitly given as an argument.
    [[ChildTicketTree(#1,border=true,root=true)]] - Show the complete tree (including original parent) within a border.
    }}}

    Args:
        ticket  - The ticket number to 'query'. The number can also be provided as a single stand alone argument. If no ticket is supplied and the macro is used within a ticket, the ticket number will be taken as the intended.
        root    - Boolean value indicating whether the parent ticket should be listed in tree (default: false).
        border  - If true, a border will be drawn around the child ticket list (default: false).

    """

    def expand_macro(self, formatter, name, text):

        req = formatter.req
        context = formatter.context
        resource = context.resource

        # Process the arguments.
        args, kwargs = parse_args(text)

        if 'ticket' not in kwargs and len(args)>0:
            kwargs['ticket'] = args[0]
        elif 'ticket' not in kwargs and not len(args):
            kwargs['ticket'] = str( WikiPage(self.env, resource).name )   # This seems to provide the correct ticket id.

        try:
            kwargs['ticket'] = int( kwargs.get('ticket').lstrip('#') )
        except ValueError:
            raise TracError('No ticket id supplied or it is not valid integer value.')

        ticket = Ticket( self.env, kwargs['ticket'] )

        self.childtickets = {}    # { parent -> children } - 1:n

        db = self.env.get_db_cnx() 
        cursor = db.cursor() 
        cursor.execute("SELECT ticket,value FROM ticket_custom WHERE name='parent'")
        for child,parent in cursor.fetchall():
            if parent and re.match('#\d+',parent):
                self.childtickets.setdefault( int(parent.lstrip('#')), [] ).append(child)

        # First ticket has no indentation.
        ticket['indent'] = '0'

        # List of tickets that will be displayed.
        if as_bool( kwargs.get('root') ):
            self.tickets = [ ticket, ]
        else:
            self.tickets = []

        # Do this neater!
        self.indent_children(ticket)

        def ticket_anchor(t):
            return tag.a( '#%s' % t.id, class_=t['status'], href=req.href.t(int(t.id)), title="%s : %s : %s" % (t['type'],t['owner'],t['status']))

        def_list = tag.dl(
                [( tag.dt(ticket_anchor(t),style='padding-left: %spx;' % (t['indent']*20)), tag.dd("%s" % t['summary'])) for t in self.tickets],
                class_='wiki compact',
                )

        if as_bool( kwargs.get('border') ):
            return tag.fieldset(
                    def_list,
                    tag.legend('Ticket Child Tree (#%s)' % ticket.id),
                    class_='description',
                    )
        else:
            return tag.div(def_list)


    def indent_children(self, ticket, indent=0):
        if ticket.id in self.childtickets:
            indent += 1
            for child in self.childtickets[ ticket.id ]:
                child = Ticket(self.env,child)
                child['indent'] = indent
                self.tickets.append(child)
                self.indent_children(child,indent)
