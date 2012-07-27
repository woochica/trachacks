# -*- coding: utf-8 -*-

from genshi.builder import tag
from genshi.filters import Transformer
from genshi.filters.transform import StreamBuffer
from trac.admin.api import IAdminPanelProvider
from trac.core import *
from trac.ticket.model import Ticket
from trac.ticket.web_ui import TicketModule
from trac.util import sorted
from trac.util.datefmt import format_datetime, to_datetime, to_timestamp, utc
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import (
    ITemplateProvider, add_ctxtnav, add_notice, add_script,
    add_stylesheet, add_warning
)

import re

class TicketDeletePlugin(Component):
    """A small ticket deletion plugin."""

    implements(IAdminPanelProvider, ITemplateProvider, ITemplateStreamFilter)

    ### ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html' and req.authname != 'anonymous':
            ticket = data.get('ticket')
            if 'TICKET_ADMIN' in req.perm(ticket.resource):
                add_stylesheet(req, 'ticketdelete/ticketdelete.css')
                buffer = StreamBuffer()

                def insert_delete_link():
                    try:
                        cnum = list(buffer)[0][1][1][0][1]
                        if cnum == "description":
                            return tag.a("Delete", title="Delete this ticket", href=("../admin/ticket/delete/%s" % ticket.id))
                        else:
                            return tag.a("Delete", title="Delete this comment", href=("../admin/ticket/comments/%s?cnum=%s" % (ticket.id, cnum)))
                    except:
                        return ""

                filter = Transformer("//div[@class='inlinebuttons']/input[@name='replyto']/@value")
                return stream | filter.copy(buffer).end() \
                                      .select("//div[@class='inlinebuttons']") \
                                      .append(insert_delete_link)
        return stream


    ### IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', 'delete', 'Delete Tickets')
            yield ('ticket', 'Ticket System', 'comments', 'Delete Changes')
            
    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('TICKET_ADMIN')
        
        data = {}
        data['href'] = req.args.has_key('referrer') and req.args['referrer'] or req.get_header('Referer') or req.href('admin', cat, page)
        data['page'] = page
        data['redir'] = 1
        data['changes'] = {}
        data['id'] = 0
        
        exists = True
        deleted = False

        if req.method == 'POST':
            if page == 'delete':
                if 'ticketid' in req.args:
                    t = self._validate(req, req.args.get('ticketid'))
                    if t:
                        self._delete_ticket(t.id)
                        self.log.debug('Deleted ticket #(%s)', t.id)
                        add_notice(req, "Ticket #%s has been deleted." % t.id)
                        deleted = True
                    else:
                        exists = False
            elif page == 'comments':
                print req.args
                if 'ticketid' in req.args:
                    t = self._validate(req, req.args.get('ticketid'))
                    if t and t.get_changelog():
                        req.redirect(req.href.admin(cat, page, t.id))
                    elif not t.get_changelog():
                        add_warning(req, "Ticket #%s has no change history" % t.id)
                    else:
                        exists = False
                else:
                    t = self._validate(req, path_info)
                    if t:
                        data['href'] = req.args.has_key('referrer') and req.args['referrer'] or req.href('admin', cat, page, path_info) 
                        
                        deletions = None
                        if "multidelete" in req.args:
                            deletions = [x.split('_') for x in req.args.getlist('mdelete')]
                            deletions.sort(lambda a,b: cmp(b[1],a[1]))
                        else:
                            buttons = [x[6:] for x in req.args.keys() if x.startswith('delete')]
                            deletions = [buttons[0].split('_')]
                            
                        if deletions:
                            for field, ts in deletions:
                                if ts != '':
                                    self.log.debug('TicketDelete: Deleting change to ticket %s at %s (%s)'% (t.id, ts, field))
                                    self._delete_change(t.id, ts, field)
                                    add_notice(req, "Change to ticket #%s at %s has been modified" % (t.id, ts))
                                    data['redir'] = 0
                    else:
                        exists = False
                    
                
        if path_info and not deleted and exists:
            t = self._validate(req, path_info)
            if t:
                if page == 'comments':
                    try:
                        selected = int(req.args.get('cnum'))
                    except (TypeError, ValueError):
                        selected = None

                    ticket_data = {}
                    for time, author, field, oldvalue, newvalue, perm in t.get_changelog():
                        ts = to_timestamp(time)
                        c_data = ticket_data.setdefault(ts, {})
                        c_data = ticket_data.setdefault(to_timestamp(time), {})
                        c_data.setdefault('fields', {})[field] = {'old': oldvalue, 'new': newvalue}
                        c_data['author'] = author
                        # FIXME: The datetime handling is not working - enable
                        # for traceback
                        c_data['prettytime'] = format_datetime(time, '%a, %x %X')
                        c_data['ts'] = ts

                    # Check the boxes next to change number `selected`
                    time_list = list(sorted(ticket_data.iterkeys()))
                    #selected isn't necessarily the same as the index because of temporary changes
                    changes = [ticket_data[time_list[i]] for i in range(0, len(time_list))]
                    if selected is not None:
                        for change in changes:
                            if change['fields'].has_key('comment') and change['fields']['comment']['old'] == str(selected):
                                change['checked'] = True
                                break

                    data['changes'] = changes
                    data['id'] = t.id
                    
                    # cnum is only in the args dictionary if we navigated from the ticket page
                    if 'cnum' in req.args:
                        add_ctxtnav(req, "Back to Ticket #%s" % t.id, req.href.ticket(t.id))

                elif page == 'delete':
                    data['id'] = t.id
 
        return 'ticketdelete_admin.html', {'ticketdelete': data}


    ### ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ticketdelete', resource_filename(__name__, 'htdocs'))]


    ### Internal methods

    def _validate(self, req, arg):
        """Validate that arg is a string containing a valid ticket ID."""
        try:
            id = int(arg)
            t = Ticket(self.env, id)
            return t
        except TracError:
            add_warning(req, "Ticket #%s not found. Please try again." % id)
        except ValueError:
            add_warning(req, "Ticket ID '%s' is not valid. Please try again." % arg)
        return False

    
    def _delete_ticket(self, id):
        """Delete the given ticket ID."""
        ticket = Ticket(self.env, id)
        ticket.delete()
            
    def _delete_change(self, id, ts, field=None):
        """Delete the change on the given ticket at the given timestamp."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        ticket = Ticket(self.env,id)
        if field:
            if field == 'attachment':
                cursor.execute("DELETE FROM attachment WHERE type = 'ticket' AND id = %s AND time = %s", (id, ts))
            else:
                custom_fields = [f['name'] for f in ticket.fields if f.get('custom')]
                if field != "comment" and not [1 for time, author, field2, oldval, newval, _ in ticket.get_changelog() if to_timestamp(time) > int(ts) and field == field2]:
                    oldval = [old for _, _, field2, old, _, _ in ticket.get_changelog(to_datetime(int(ts))) if field2 == field][0]
                    if field in custom_fields:
                        cursor.execute("UPDATE ticket_custom SET value=%s WHERE ticket=%s AND name=%s", (oldval, id, field))
                    else:
                        cursor.execute("UPDATE ticket SET %s=%%s WHERE id=%%s" % field, (oldval, id))
                cursor.execute("DELETE FROM ticket_change WHERE ticket = %s AND time = %s AND field = %s", (id, ts, field))
        else:
            for _, _, field, _, _, _ in ticket.get_changelog(to_datetime(int(ts), utc)):
                self._delete_change(id, ts, field)
            
        db.commit()
