# Authentication crosslink module
# Copyright 2006 Noah Kantrowitz

from trac.core import *
from trac.config import Option
from trac.web.auth import LoginModule
from trac.web.main import _open_environment
from trac.env import Environment
from trac.web.href import Href
from trac.util.html import escape, html
from trac.web.api import IRequestFilter, Request

class TracForgeLoginModule(LoginModule):
    """Replacement for LoginModule to slave to another environment."""
    
    master_path = Option('tracforge', 'master_path',
                         doc='Path to master Trac')

    master_env = property(lambda self: _open_environment(self.master_path))
    master_href = property(lambda self: Href(self.master_env.base_url))
            
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'login'

    def get_navigation_items(self, req):
        if req.authname and req.authname != 'anonymous':
            yield ('metanav', 'login', 'logged in as %s' % req.authname)
            yield ('metanav', 'logout',
                   html.A('Logout', href=self.master_href.logout()))
        else:
            yield ('metanav', 'login',
                   html.A('Login', href=self.master_href.login()))

    # Internal methods
    def _get_name_for_cookie(self, req, cookie):
        return LoginModule(self.master_env)._get_name_for_cookie(req, cookie)

class TracForgeCookieMunger(Component):
    
    uri_root = Option('tracforge', 'uri_root', default='/',
                      doc='The smallest common URI for the whole TracForge setup')
                      
    implements(IRequestFilter)

    def pre_process_request(self, req, handler):
        self.log.debug('TracForgeCookieMunger: Running')
        if req.path_info.startswith('/login'):
            self.log.debug('TracForgeCookieMunger: Path match')
            def my_redirect(*args, **kwords):
                self.log.debug('TracForgeCookieMunger: Captured redirect!')
                self.log.debug('TracForgeCookieMunger: Pre munging\n%s'%req.outcookie)
                if 'trac_auth' in req.outcookie:
                    req.outcookie['trac_auth']['path'] = self.uri_root
                self.log.debug('TracForgeCookieMunger: Post munging\n%s'%req.outcookie)
                Request.redirect(req, *args, **kwords)
            
            assert repr(req.redirect).startswith('<bound method')
            req.redirect = my_redirect
            
        return handler
        
    def post_process_request(self, req, template, content_type):
        #if req.path_info.startswith('/login'):
        #    if 'trac_auth' in req.outcookie:
        #        req.outcookie['trac_auth']['path'] = self.uri_root
        return (template, content_type)
