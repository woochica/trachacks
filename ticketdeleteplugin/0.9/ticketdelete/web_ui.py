# Ticket deleting plugins

from trac import __version__ as TRAC_VERSION
from trac.core import *
from trac.ticket.model import Ticket
from trac.web.chrome import ITemplateProvider
from webadmin.web_ui import IAdminPageProvider
import re

__all__ = ['TicketDeletePlugin']

class TicketDeletePlugin(Component):
    """A small ticket deletion plugin."""
    
    implements(ITemplateProvider, IAdminPageProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            yield ('ticket', 'Ticket System', 'delete', 'Delete')
            
    def process_admin_request(self, req, cat, page, path_info):
        assert req.perm.has_permission('TICKET_ADMIN')
        
        if req.method == 'POST':
            if 'ticketid' in req.args and 'ticketid2' in req.args:
                if req.args.get('ticketid') == req.args.get('ticketid2'):
                    try:
                        id = int(req.args.get('ticketid'))
                        t = Ticket(self.env, id)
                        self._delete_ticket(id)
                        req.hdf['ticketdelete.message'] = "Ticket #%s has been deleted." % id
                    except TracError:
                        req.hdf['ticketdelete.message'] = "Ticket #%s not found. Please try again." % id
                    except ValueError:
                        req.hdf['ticketdelete.message'] = "Ticket ID '%s' is not valid. Please try again." % req.args.get('ticketid')
                else:
                    req.hdf['ticketdelete.message'] = "The two IDs did not match. Please try again."
        req.hdf['ticketdelete.href'] = self.env.href('admin','ticket','delete')
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
        return [('ticketdelete', resource_filename(__name__, 'htdocs'))]


    # Internal methods
    def _delete_ticket(self, id):
        md = re.match('(\d+)\.(\d+)',TRAC_VERSION)
        if md and (int(md.group(2)) >= 10 or int(md.group(1)) > 0):
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
