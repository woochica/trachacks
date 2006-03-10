# CASified login module for Trac

from trac.core import *
from trac.web.api import IAuthenticator, IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.util import escape, hex_entropy, Markup
from trac.web.auth import LoginModule
from pycas import PyCAS

class CasLoginModule(LoginModule):
    """A CAS-based login module."""
    
    def __init__(self):
        url = self.config.get('cas','server').strip()
        paths = {
            'login_path': self.config.get('cas','login_path','/login').strip(),
            'logout_path': self.config.get('cas','logout_path','/logout').strip(),
            'validate_path': self.config.get('cas','validate_path','/validate').strip(),
        }
        self.cas = PyCAS(url, **paths)
        self.service = self.env.abs_href.login()
        
    # IAuthenticatorMethods
    def authenticate(self, req):
        ticket = req.args.get('ticket')
        if ticket:
            valid, user = self.cas.validate_ticket(self.service, ticket)
            if valid:
                req.remote_user = user
                
        return super(CasLoginModule, self).authenticate(req)
        
    # INavigationContributor methods
    def get_navigation_items(self, req):        
        if req.authname and req.authname != 'anonymous':
            yield ('metanav', 'login', 'logged in as %s' % req.authname)
            yield ('metanav', 'logout', Markup('<a href="%s">Logout</a>' % escape(self.env.href.logout())))
        else:
            yield ('metanav', 'login', Markup('<a href="%s">Login</a>' % escape(self.cas.login_url(self.service))))
        

    def _do_logout(self, req):
        super(CasLoginModule, self)._do_logout(req)
        req.redirect(self.cas.logout_url(self.env.abs_href()))

