# Ticket deleting plugins

from trac import __version__ as TRAC_VERSION
from trac.core import *
from trac.ticket.model import Ticket
from trac.web.chrome import ITemplateProvider
from webadmin.web_ui import IAdminPageProvider
import re, traceback
from time import strftime, localtime

__all__ = ['TicketDeletePlugin']

class TicketDeletePlugin(Component):
    """A small ticket deletion plugin."""
    
    implements(ITemplateProvider, IAdminPageProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            yield ('ticket', 'Ticket System', 'delete', 'Delete')
            yield ('ticket', 'Ticket System', 'comments', 'Delete Changes')
            
    def process_admin_request(self, req, cat, page, path_info):
        assert req.perm.has_permission('TICKET_ADMIN')
        
        req.hdf['ticketdelete.href'] = self.env.href('admin', cat, page)
        req.hdf['ticketdelete.page'] = page
        req.hdf['ticketdelete.redir'] = 1

        if req.method == 'POST':
            if page == 'delete':
                if 'ticketid' in req.args and 'ticketid2' in req.args:
                    if req.args.get('ticketid') == req.args.get('ticketid2'):
                        t = self._validate(req, req.args.get('ticketid'))
                        if t:
                            self._delete_ticket(t.id)
                            req.hdf['ticketdelete.message'] = "Ticket #%s has been deleted." % t.id
                            
                    else:
                        req.hdf['ticketdelete.message'] = "The two IDs did not match. Please try again."
            elif page == 'comments':
                if 'ticketid' in req.args:
                    req.redirect(self.env.href.admin(cat, page, req.args.get('ticketid')))
                else:
                    t = self._validate(req, path_info)
                    if t:
                        req.hdf['ticketdelete.href'] = self.env.href('admin', cat, page, path_info)
                        try:
                            buttons = None
                            if "multidelete" in req.args:
                                buttons = req.args.getlist('delete')
                            else:
                                buttons = [x[6:] for x in req.args.keys() if x.startswith('delete')]
                            if buttons:
                                for button in buttons:
                                    field, ts = button.split('_')
                                    ts = int(ts)
                                    self.log.debug('TicketDelete: Deleting change to ticket %s at %s (%s)'%(t.id,ts,field))
                                    self._delete_change(t.id, ts, field)
                                    req.hdf['ticketdelete.message'] = "Change to ticket #%s at %s has been modified" % (t.id, strftime('%a, %d %b %Y %H:%M:%S',localtime(ts)))
                                    req.hdf['ticketdelete.redir'] = 0
                        except ValueError:
                            req.hdf['ticketdelete.message'] = "Timestamp '%s' not valid" % req.args.get('ts')
                            self.log.debug(traceback.format_exc())
                    
                    
                
        if page == 'comments':
            if path_info:
                t = self._validate(req, path_info)
                if t:
                    for time, author, field, oldvalue, newvalue in t.get_changelog():
                        req.hdf['ticketdelete.changes.%s.fields.%s'%(time,field)] = {'old': oldvalue, 'new': newvalue}
                        req.hdf['ticketdelete.changes.%s.author'%time] = author
                        req.hdf['ticketdelete.changes.%s.prettytime'%time] = strftime('%a, %d %b %Y %H:%M:%S',localtime(time))
                    
                
        return 'ticketdelete_admin.cs', None

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
        #return [('ticketdelete', resource_filename(__name__, 'htdocs'))]
        return []


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
            req.hdf['ticketdelete.message'] = "Ticket #%s not found. Please try again." % id
        except ValueError:
            req.hdf['ticketdelete.message'] = "Ticket ID '%s' is not valid. Please try again." % arg
        return False
                                                                                                                
    
    def _delete_ticket(self, id):
        """Delete the given ticket ID."""
        major, minor = self._get_trac_version()
        if major > 0 or minor >= 10:
            ticket = Ticket(self.env,id)
            ticket.delete()
        else:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("DELETE FROM ticket WHERE id=%s", (id,))
            cursor.execute("DELETE FROM ticket_change WHERE ticket=%s", (id,))
            cursor.execute("DELETE FROM attachment WHERE type='ticket' and id=%s", (id,))
            cursor.execute("DELETE FROM ticket_custom WHERE ticket=%s", (id,))
            db.commit()
            
    def _delete_change(self, id, ts, field=None):
        """Delete the change on the given ticket at the given timestamp."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        ticket = Ticket(self.env,id)
        if field:
            custom_fields = [f['name'] for f in ticket.fields if f.get('custom')]
            if field != "comment" and not [1 for time, author, field2, oldval, newval in ticket.get_changelog() if time > ts and field == field2]:
                oldval = [old for _, _, field2, old, _ in ticket.get_changelog(ts) if field2 == field][0]
                if field in custom_fields:
                    cursor.execute("UPDATE ticket_custom SET value=%s WHERE ticket=%s AND name=%s", (oldval, id, field))
                else:
                    cursor.execute("UPDATE ticket SET %s=%%s WHERE id=%%s" % field, (oldval, id))
            cursor.execute("DELETE FROM ticket_change WHERE ticket = %s AND time = %s AND field = %s", (id, ts, field))
        else:
            for _, _, field, _, _ in ticket.get_changelog(ts):
                self._delete_change(id, ts, field)
            
        db.commit()
