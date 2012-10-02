# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag
from genshi.filters import Transformer
from trac.admin.api import IAdminPanelProvider
from trac.core import Component, TracError, implements
from trac.ticket.model import Ticket
from trac.util import sorted
from trac.util.datefmt import format_datetime, to_datetime, to_timestamp
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import (
    ITemplateProvider, add_ctxtnav, add_notice, add_warning
)

class TicketDeletePlugin(Component):
    implements(IAdminPanelProvider, IRequestFilter, ITemplateProvider,
               ITemplateStreamFilter)

    ### IRequestFilter methods

    def pre_process_request(self, req, handler):
        if req.path_info.startswith('/ticket/') and req.args.get('delete'):
            id = req.args.get('id')
            cnum = req.args.get('replyto')
            if not cnum or cnum == 'description':
                href = req.href('/admin/ticket/deleteticket', id)
            else:
                href = req.href('/admin/ticket/deletechange', id, cnum=cnum)
            req.redirect(href)
        return handler

    def post_process_request(self, req, template, content_type):
        return template, content_type


    ### ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        ticket = data.get('ticket')
        if filename == 'ticket.html' and 'TICKET_ADMIN' in req.perm(ticket.resource):

            # Add Delete button to ticket description
            if data['ticket'].values['description']:
                # Reply button and associated elements are present
                filter = Transformer("//div[@class='description']//div[@class='inlinebuttons']")
                stream |= filter.append(tag.input(type='submit', name='delete',
                                                  title="Delete this ticket", value='Delete'))
            else:
                # Reply button and associated elements not present
                filter = Transformer("//div[@class='description']/h3")
                stream |= filter.after( \
                    tag.form(tag.div(tag.input(type='submit', name='delete',
                                               title="Delete this ticket", value='Delete'),
                                     class_='inlinebuttons'
                                     ),
                             name='addreply', method='get', action='#comment')
                             )

            # Add Delete buttons to ticket comments
            stream |= Transformer("//div[@id='changelog']//div[@class='inlinebuttons']") \
                          .append(tag.input(type='submit', name='delete',
                                            title="Delete this comment", value='Delete'))

        return stream


    ### IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', 'deletechange', 'Delete Changes')
            yield ('ticket', 'Ticket System', 'deleteticket', 'Delete Tickets')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('TICKET_ADMIN')

        data = {
            'changes': {},
            'id': None,
            'page': page,
        }
        
        exists = True
        deleted = False

        if req.method == 'POST':
            if page == 'deleteticket':
                if 'ticketid' in req.args:
                    t = self._validate(req, req.args.get('ticketid'))
                    if t:
                        self._delete_ticket(t.id)
                        add_notice(req, "Ticket #%s has been deleted." % t.id)
                        deleted = True
                    else:
                        exists = False
            elif page == 'deletechange':
                if 'ticketid' in req.args and req.args.get('ticketid'):
                    t = self._validate(req, req.args.get('ticketid'))
                    if t:
                        if t.get_changelog():
                            req.redirect(req.href.admin(cat, page, t.id))
                        else:
                            add_warning(req, "Ticket #%s has no change history" % t.id)
                    else:
                        exists = False
                else:
                    t = self._validate(req, path_info)
                    if t:
                        deletions = None
                        if 'multidelete' in req.args:
                            deletions = [x.split('_') for x in req.args.getlist('mdelete')]
                            deletions.sort(lambda a,b: cmp(b[1],a[1]))
                        else:
                            buttons = [x[7:] for x in req.args.keys() if x.startswith('delete')]
                            deletions = [buttons[0].split('_')]
                        if deletions:
                            for field, ts in deletions:
                                if field == 'change':
                                    self._delete_change(t.id, ts)
                                else:
                                    self._delete_change(t.id, ts, field)
                                add_notice(req, "Change(s) to ticket #%s at %s has been deleted." % (t.id, format_datetime(int(ts))))
                    else:
                        exists = False

        tid = path_info or req.args.get('ticketid')
        if tid and not deleted and exists:
            t = self._validate(req, tid)
            if t:
                data['id'] = t.id
                if page == 'deletechange':

                    # Get a dictionary of changes, using the timestamp as a key to use for sorting
                    ticket_data = {}
                    for time, author, field, oldvalue, newvalue, perm in t.get_changelog():
                        ts = to_timestamp(time)
                        c_data = ticket_data.setdefault(ts, {})
                        c_data.setdefault('fields', {})[field] = {'old': oldvalue, 'new': newvalue}
                        c_data['author'] = author
                        c_data['ts'] = ts
                    # Sort the dictionary of changes into a list.
                    changes = [ticket_data[k] for k in sorted(ticket_data.iterkeys())]

                    # Check the boxes next to change number `checked`
                    # Selected isn't necessarily the same as the index because of temporary changes
                    checked = req.args.get('cnum')
                    if checked:
                        for change in changes:
                            if 'comment' in change['fields'] and change['fields']['comment']['old'] == checked:
                                change['checked'] = True
                                break

                    data['changes'] = changes

                add_ctxtnav(req, "Back to Ticket #%s" % t.id, req.href.ticket(t.id))

        return 'ticketdelete_admin.html', {'ticketdelete': data}


    ### ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return []


    ### Internal methods

    def _validate(self, req, arg):
        """Validate that arg is a string containing a valid ticket ID."""
        if not arg:
            add_warning(req, "Ticket ID was not entered.")
            return False
        try:
            id = int(arg.lstrip('#'))
            t = Ticket(self.env, id)
            return t
        except TracError:
            if id > 0:
                add_warning(req, "Ticket #%s does not exist." % id)
            else:
                add_warning(req, "'%s' is not a valid ticket ID." % id)
        except ValueError:
            add_warning(req, "'%s' is not a valid ticket ID." % arg)
        return False

    def _delete_ticket(self, id):
        """Delete the given ticket ID."""
        ticket = Ticket(self.env, id)
        ticket.delete()
        self.log.debug("Deleted ticket #%s" % id)
            
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
                        cursor.execute("""
                            UPDATE ticket_custom SET value=%s
                            WHERE ticket=%s AND name=%s""", (oldval, id, field))
                    else:
                        cursor.execute("""
                            UPDATE ticket SET %s=%%s
                            WHERE id=%%s""" % field, (oldval, id))
                cursor.execute("""
                    DELETE FROM ticket_change
                    WHERE ticket = %s AND time = %s AND field = %s
                    """, (id, ts, field))
            self.log.debug('TicketDelete: Deleted change to ticket %s at %s (%s)' % (id, ts, field))
        else:
            for _, _, field, _, _, _ in ticket.get_changelog(to_datetime(int(ts))):
                self._delete_change(id, ts, field)

        db.commit()

