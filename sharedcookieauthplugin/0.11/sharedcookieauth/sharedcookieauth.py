"""
SharedCookieAuth:
a plugin for Trac to share cookies between Tracs
http://trac.edgewall.org
"""

import os

from trac.core import *
from trac.web.api import IAuthenticator
from trac.web import auth
from trac.web.main import RequestDispatcher
from trac.env import open_environment
from trac.env import IEnvironmentSetupParticipant

class GenericObject(object):
    def __init__(self, **kw):
        for key, item in kw.items():
            setattr(self, key, item)

def _do_login(self, req):
    kw = [ 'incookie', 'remote_user', 'authname', 
           'remote_addr', 'outcookie' ]
    kw = dict([ (i, getattr(req, i)) for i in kw ])
    kw['base_path'] = '/'
    fake_req = GenericObject(**kw)
    auth_login_module_do_login(self, fake_req)

class SharedCookieAuth(Component):

    implements(IAuthenticator, IEnvironmentSetupParticipant)
    patched = False

    def authenticate(self, req):
        if req.incookie.has_key('trac_auth'):
            base_path, project = os.path.split(self.env.path)
            _projects = [ i for i in os.listdir(base_path)
                          if i != project ]
            projects = []
            for _project in _projects:
                path = os.path.join(base_path, _project)
                try:
                    projects.append(open_environment(path))
                except:
                    continue
            for project in projects:
                rd = RequestDispatcher(project)
                agent = rd.authenticate(req)
                if agent != 'anonymous':
                    return agent
        return None

    def _do_login(self, req):
        if not req.remote_user:
            req.redirect(self.env.abs_href())
        base_path = req.base_path
        req.base_path = '/'
        retval = auth.LoginModule._do_login(self, req)
        req.base_path = base_path
        return retval

    ### methods for IEnvironmentSetupParticipant

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created(self):
        """Called when a new Trac environment is created."""

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        if not self.patched:
            globals()['auth_login_module_do_login'] = auth.LoginModule._do_login
            auth.LoginModule._do_login = _do_login
            self.patched = True
        return False
        

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """


