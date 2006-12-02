from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.web.main import IRequestFilter
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider, add_script
from trac.util.html import Markup

import inspect

__all__ = ['FakeUsernameFilter']

class FakeUsernameFilter(Component):
    """A request filter to allow lying about the person submitting a ticket."""
    
    implements(IRequestFilter, IPermissionRequestor, ITemplateProvider, ITicketChangeListener)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, content_type):
        if self._change_req(req):
            add_script(req, 'fakeusername/jquery.js')
            add_script(req, 'fakeusername/fakeusername.js')
            req.hdf['project.footer'] = Markup('%s <span id="fakeusername_evil" style="display:none">%s</span>'%(req.hdf['project.footer'], req.authname))
    
        return template, content_type

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_FAKE_USERNAME'

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('fakeusername', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
        
    # ITicketChangeListener methods
    def ticket_created(self, ticket):
        req = None
        for x in inspect.stack():
            if 'req' in x[0].f_locals:
                req = x[0].f_locals['req']
                if req is not None:
                    break
        
        if req is None:
            raise TracError('Penguins on fire: Unable to extract req')

        reporter = req.args.get('reporter')
        if self._change_req(req) and reporter:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            # XXX: Very brittle <NPK>
            cursor.execute('UPDATE ticket SET reporter=%s WHERE id=%s', (reporter, ticket.id))
            db.commit()
            
    def ticket_changed(self, ticket, comment, author, old_values):
        pass
   
    def ticket_deleted(self, ticket):
        pass

    # Internal methods
    def _change_req(self, req):
        return req.path_info.startswith('/newticket') and \
               req.authname != 'anonymous' and \
               (req.perm.has_permission('TICKET_FAKE_USERNAME') or req.perm.has_permission('TICKET_ADMIN'))
