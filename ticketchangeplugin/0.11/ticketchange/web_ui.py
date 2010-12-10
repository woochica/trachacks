# Ticket changing plugins

import re

from genshi.builder import tag
from genshi.filters import Transformer
from genshi.filters.transform import StreamBuffer

from trac.core import *
from trac.resource import ResourceNotFound
from trac.ticket.model import Ticket
from trac.util.datefmt import format_datetime, to_timestamp
from trac.web import IRequestHandler
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script, add_stylesheet, ITemplateProvider
from trac.wiki import wiki_to_html

__all__ = ['TicketChangePlugin']

class TicketChangePlugin(Component):
    """A small ticket change plugin."""
    
    implements(ITemplateProvider, ITemplateStreamFilter, IRequestHandler)

    # ITemplateStreamFilter methods	
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html' and req.authname != 'anonymous':
            ticket = data.get('ticket')
            if req.perm.has_permission('TICKET_ADMIN'):
    	        self.log.debug("TicketChangePlugin adding 'Change' links for ticket %s" % ticket.id)
                buffer = StreamBuffer()
                
                def insert_change_link():
                    cnum = list(buffer)[0][1][1][0][1]
                    return tag(" ", tag.a("Change", href=("../ticketchangecomment/%s?cnum=%s" % (ticket.id, cnum))))

                filter = Transformer("//div[@class='change']/div[@class='inlinebuttons']/input[@name='replyto']/@value")
                return stream | filter.copy(buffer).end() \
                              .select("//div[@class='change']/div[@class='inlinebuttons']/input[@value='Reply']") \
                              .after(insert_change_link)
        return stream

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'^/ticketchangecomment(?:/(.*))?', req.path_info)
        if match:
            if match.group(1):
                req.args['ticketid'] = match.group(1)
            return True

    def process_request(self, req):
        req.perm.require('TICKET_ADMIN')

        ticketchange = {}
        ticketchange['href'] = self.env.href('report')
        ticketchange['redir'] = 1

        ticketid = req.args.get('ticketid')
        if not ticketid:
            ticketchange['message'] = "Ticket ID is not specified. Please try again."
            ticket = None
        else:
            ticket = self._validate(req, ticketid)

        ticketchange = {}
        if ticket:
            if req.method == 'POST':
                comment = req.args.get('comment')
                if req.args.has_key('preview'):
                    if comment:
                        ticketchange['change'] = {}
                        ticketchange['change']['time'] = int(req.args.get('time'))
                        ticketchange['change']['author'] = req.args.get('author')                        
                        ticketchange['change']['fields'] = {}
                        ticketchange['change']['fields']['comment'] = {}
                        ticketchange['change']['fields']['comment']['new'] = comment
                        # Wiki format a preview of comment
                        db = self.env.get_db_cnx()
                        ticketchange['comment_preview'] = wiki_to_html(comment, self.env, 
                                                                       req, db, escape_newlines=True)
                        ticketchange['href'] = req.args.get('href')
                        ticketchange['href2'] = req.args.get('href2')
                else:
                    if not req.args.has_key('cancel'):
                        time = int(req.args.get('time'))
                        self._update_ticket_comment(ticket.id, time, comment, req.authname)
                    req.redirect(req.args.get('href2'))

                    #We're redirecting  - this shouldn't do anything
                    return 'ticket.html', None, None
            else:
                cnum = req.args.get('cnum')
                if not cnum:
                    ticketchange['href'] = self.env.href.ticket(ticketid)
                    ticketchange['message'] = "Ticket change is not specified. Please try again."
                else:
                    ticketchange['href'] = self.env.href.ticket(ticketid) + '#comment:' + cnum

                selected_time = None
                ticket_data = {}
                for time, author, field, oldvalue, newvalue, perm in ticket.get_changelog():
                    data = ticket_data.setdefault(str(time), {})
                    data.setdefault('fields', {})[field] = {'old': oldvalue, 'new': newvalue}
                    data['time'] = to_timestamp(time);
                    data['author'] = author
                    if field == 'comment' and oldvalue.rsplit('.', 1)[-1] == cnum :
                        selected_time = str(time)

                # Remove all attachment changes                    
                for k, v in ticket_data.items():
                    if 'attachment' in v.get('fields', {}):
                        del ticket_data[k]
                    
                if selected_time and ticket_data.has_key(selected_time):
                    ticketchange['change'] = ticket_data[selected_time]
                    ticketchange['href'] = self.env.href(req.path_info)
                    ticketchange['href2'] = self.env.href.ticket(ticketid) + '#comment:' + cnum
                else:
                    ticketchange['message'] = "Ticket change '%s' not found. Please try again." % cnum
 
        return 'ticketchangecomment.html', {'ticket': ticket, 'ticketchange': ticketchange}, None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []


    # Internal methods
    def _validate(self, ticketchange, arg):
        """Validate that arg is a string containing a valid ticket ID."""
        try:
            id = int(arg)
            t = Ticket(self.env, id)
            return t
        except TracError:
            ticketchange['message'] = "Ticket #%s not found. Please try again." % id
        except ValueError:
            ticketchange['message'] = "Ticket ID '%s' is not valid. Please try again." % arg
        return False

    def _update_ticket_comment(self, id, time, comment, author):
        """Update ticket change comment"""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT author, newvalue FROM ticket_change WHERE ticket = %s AND time = %s AND field = 'comment'", (id, time))
        row = cursor.fetchone()
        if not row:
            raise ResourceNotFound("Unable to update comment %d (%s) on Ticket #%d - comment not found.\n" \
                                   % (time, format_datetime(time), id))
        old_author, old_comment = (row[0], row[1])
        cursor.execute("UPDATE ticket_change SET newvalue=%s WHERE ticket = %s AND time = %s AND field = 'comment'", (comment, id, time))
        db.commit()
        
        self.env.log.info("Ticket #%d comment %d (%s) by %s has been updated by %s.\n"
                          "old value:\n%s\n\nnew value:\n%s\n" \
                        % (id, time, format_datetime(time), old_author, author, 
                           old_comment.replace('\r', ''), comment.replace('\r','')))
                                                                                                                

