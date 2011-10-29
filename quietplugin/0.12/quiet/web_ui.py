import json
from trac.core import *
from genshi.builder import tag
from trac.web.chrome import add_script, add_stylesheet, add_ctxtnav
from trac.web.chrome import ITemplateProvider
from trac.web.main import IRequestFilter, IRequestHandler
from trac.perm import IPermissionRequestor
from trac.config import Option
from trac.util.translation import _

NAME = 'quietmode'

# WARNING: dependency on Announcer plugin!
from announcer.distributors.mail import EmailDistributor
class QuietEmailDistributor(EmailDistributor):
    """"Specializes Announcer's email distributor to honor quiet mode."""
    def distribute(self, transport, recipients, event):
        if hasattr(event,'author') and self._is_quiet_mode(event.author):
            return
        EmailDistributor.distribute(self, transport, recipients, event)
    
    def _is_quiet_mode(self, user):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT value
              FROM session_attribute
             WHERE sid=%s
               AND name=%s
        """, (user,NAME))
        result = cursor.fetchone()
        if not result:
            return False
        return result[0] == '1'
        

class QuietBase(object):
    """Shared class for common methods."""
    
    enter_label = Option('quiet', 'enter_label', _('Enter Quiet Mode'))
    leave_label = Option('quiet', 'leave_label', _('Leave Quiet Mode'))
    
    def _is_quiet(self, req):
        """Returns true if the user requested quiet mode."""
        val = req.session.get(NAME, '0')
        return val == '1'
    
    def _get_label(self, req, is_quiet=None):
        if is_quiet is None:
            is_quiet = self._is_quiet(req)
        return is_quiet and _(self.leave_label) or _(self.enter_label)
    
    def _toggle_quiet(self, req):
        """Set or unset quiet mode for the user."""
        val = self._is_quiet(req) and '0' or '1' # toggle value
        req.session[NAME] = val
        req.session.save()
        return val == '1'


class QuietModule(Component,QuietBase):
    implements(IRequestHandler, IRequestFilter,
               ITemplateProvider, IPermissionRequestor)
        
    # IPermissionRequestor methods  
    def get_permission_actions(self):
        return ['QUIET_MODE']

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('quiet', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if req.perm.has_permission('QUIET_MODE') and \
           (req.path_info.startswith('/ticket') or \
            req.path_info.startswith('/newticket') or \
            req.path_info.startswith('/query') or \
            req.path_info.startswith('/report')):
            href = req.href(NAME,'toggle')
            a = tag.a(self._get_label(req), href=href, id=NAME)
            add_ctxtnav(req, a)
            add_script(req, '/quiet/quiet.html')
            add_stylesheet(req, 'quiet/quiet.css')
        return template, data, content_type
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/quiet/')
    
    def process_request(self, req):
        req.perm.require('QUIET_MODE')
        return 'quiet.html', {'id':NAME}, 'text/javascript'


class QuietAjaxModule(Component,QuietBase):
    implements(IRequestHandler)
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/'+NAME)
    
    def process_request(self, req):
        try:
            if 'toggle' in req.path_info:
                is_quiet = self._toggle_quiet(req)
            else:
                is_quiet = self._is_quiet(req)
            data = {'label':self._get_label(req, is_quiet),
                    'is_quiet':is_quiet}
            code,msg = 200,json.dumps(data)
        except Exception, e:
            import traceback;
            code,msg = 500,"Oops...\n" + traceback.format_exc()+"\n"
        req.send_response(code)
        req.send_header('Content-Type', 'text/plain')
        req.send_header('Content-Length', len(msg))
        req.end_headers()
        req.write(msg);
