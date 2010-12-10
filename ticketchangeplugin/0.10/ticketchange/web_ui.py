# Ticket changing plugins

from trac import __version__ as TRAC_VERSION
from trac.core import *
from trac.ticket.model import Ticket
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.web import IRequestHandler
from trac.util import sorted 
from trac.wiki import wiki_to_html

import re
import traceback
import pprint
from time import strftime, localtime

__all__ = ['TicketChangePlugin']

class TicketChangePlugin(Component):
    """A small ticket change plugin."""
    
    implements(ITemplateProvider, IRequestFilter, IRequestHandler)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, content_type):
        if template == 'ticket.cs' and req.perm.has_permission('TICKET_ADMIN'):
            add_script(req, 'ticketdelete/jquery.js')
            add_script(req, 'ticketdelete/ticketdelete.js')
            add_stylesheet(req, 'ticketdelete/ticketdelete.css')
            add_script(req, 'ticketchange/ticketchange.js')
        return template, content_type
 
    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'^/ticketchangecomment(?:/(.*))?', req.path_info)
        if match:
            if match.group(1):
                req.args['ticketid'] = match.group(1)
            return True

    def process_request(self, req):
        req.perm.assert_permission('TICKET_ADMIN')
        
        req.hdf['ticketchange.href'] = self.env.href('report')
        req.hdf['ticketchange.redir'] = 1

        ticketid = req.args.get('ticketid')
        if not ticketid:
            req.hdf['ticketchange.message'] = "Ticket ID is not specified. Please try again."
            ticket = None
        else:
            ticket = self._validate(req, ticketid)

        if ticket:
            if req.method == 'POST':
                comment = req.args.get('comment')
                if req.args.has_key('preview'):
                    if comment:
                        req.hdf['ticketchange.change.fields.comment.new'] = comment
                        # Wiki format a preview of comment
                        db = self.env.get_db_cnx()
                        req.hdf['ticketchange.comment_preview'] = wiki_to_html(
                            comment, self.env, req, db)
                        req.hdf['ticketchange.change.time'] = req.args.get('time')
                        req.hdf['ticketchange.change.prettytime'] = req.args.get('prettytime')
                        req.hdf['ticketchange.change.author'] = req.args.get('author')
                        req.hdf['ticketchange.href'] = req.args.get('href')
                        req.hdf['ticketchange.href2'] = req.args.get('href2')
                else:
                    time = int(req.args.get('time'))
                    self._update_ticket_comment(ticket.id, time, comment, req.authname)
                    req.redirect(req.args.get('href2'))
                    return 'ticket.cs', None
            else:
                cnum = req.args.get('cnum')
                if not cnum:
                    req.hdf['ticketchange.href'] = self.env.href.ticket(ticketid)
                    req.hdf['ticketchange.message'] = "Ticket change is not specified. Please try again."
                else:
                    req.hdf['ticketchange.href'] = self.env.href.ticket(ticketid) + '#comment:' + cnum

                selected_time = None
                ticket_data = {}
                for time, author, field, oldvalue, newvalue, perm in ticket.get_changelog():
                    data = ticket_data.setdefault(str(time), {})
                    data.setdefault('fields', {})[field] = {'old': oldvalue, 'new': newvalue}
                    data['time'] = time
                    data['author'] = author
                    data['prettytime'] = strftime('%A, %d %b %Y %H:%M:%S', localtime(time))
                    if field == 'comment' and oldvalue.rsplit('.', 1)[-1] == cnum :
                        selected_time = str(time)

                # Remove all attachment changes                    
                for k, v in ticket_data.items():
                    if 'attachment' in v.get('fields', {}):
                        del ticket_data[k]
                    
                if selected_time :
                    req.hdf['ticketchange.change'] = ticket_data[selected_time]
                    req.hdf['ticketchange.href'] = self.env.href(req.path_info)
                    req.hdf['ticketchange.href2'] = self.env.href.ticket(ticketid) + '#comment:' + cnum
                else:
                    req.hdf['ticketchange.message'] = "Ticket change '%s' not found. Please try again." % cnum
 
        return 'ticketchangecomment.cs', None

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
        from pkg_resources import resource_filename
        return [('ticketchange', resource_filename(__name__, 'htdocs'))]

    # Internal methods
    def _get_trac_version(self):
        md = re.match('(\d+)\.(\d+)',TRAC_VERSION)
        if md:
            return (int(md.group(1)),int(md.group(2)))
        else:
            return (0,0)

    def _validate(self, req, arg):
        """Validate that arg is a string containing a valid ticket ID."""
        try:
            id = int(arg)
            t = Ticket(self.env, id)
            return t
        except TracError:
            req.hdf['ticketchange.message'] = "Ticket #%s not found. Please try again." % id
        except ValueError:
            req.hdf['ticketchange.message'] = "Ticket ID '%s' is not valid. Please try again." % arg
        return False

    def _update_ticket_comment(self, id, time, comment, author):
        """Update ticket change comment"""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT author, newvalue FROM ticket_change WHERE ticket = %s AND time = %s AND field = 'comment'", (id, time))
        old_author, old_comment = cursor.fetchall()[0]
        cursor.execute("UPDATE ticket_change SET newvalue=%s WHERE ticket = %s AND time = %s AND field = 'comment'", (comment, id, time))
        db.commit()
        self.env.log.info("Ticket #%d comment of '%s' by '%s' has been updated by '%s':\nold value: '%s'\n\nnew value: '%s'\n" \
                        % (id, strftime('%A, %d %b %Y %H:%M:%S', localtime(time)), old_author, author, old_comment.replace('\r', ''), comment.replace('\r','')))
                                                                                                                
