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

from urlparse import urlsplit
import inspect

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
                   html.A('Logout', href=self.master_href.logout(referer=req.href(req.path_info))))
        else:
            yield ('metanav', 'login',
                   html.A('Login', href=self.master_href.login(referer=req.href(req.path_info))))

    # Internal methods
    def _get_name_for_cookie(self, req, cookie):
        return LoginModule(self.master_env)._get_name_for_cookie(req, cookie)

class TracForgeCookieMunger(Component):
    
    uri_root = Option('tracforge', 'uri_root', default='/',
                      doc='The smallest common URI for the whole TracForge setup')
                      
    real_get_header = Request.get_header
                      
    implements(IRequestFilter)

    def __init__(self):
        #Request.get_header = self._my_get_header
        pass

    def pre_process_request(self, req, handler):
        #self.log.debug('TracForgeCookieMunger: Running')
        if req.path_info.startswith('/login') or req.path_info.startswith('/logout'):
            #self.log.debug('TracForgeCookieMunger: Path match')
            def my_redirect(*args, **kwords):
                #self.log.debug('TracForgeCookieMunger: Captured redirect!')
                #self.log.debug('TracForgeCookieMunger: Pre munging\n%s'%req.outcookie)
                if 'trac_auth' in req.outcookie:
                    assert not self.uri_root.startswith('http'), 'The tracforge uri_root must be set to relative path'
                    req.outcookie['trac_auth']['path'] = self.uri_root
                #self.log.debug('TracForgeCookieMunger: Post munging\n%s'%req.outcookie)

                referer = req.args.get('referer')
                self.log.debug('TracForgeCookieMunger: Got referer as %r'%referer)
                if referer:
                    parts = urlsplit(referer or '')
                    self.log.debug('TracForgeCookieMunger: parts=%s name=%r'%(parts,req.server_name))
                    if parts[2].startswith(self.uri_root) and (not parts[1] or parts[1] == req.server_name):
                        Request.redirect(req, referer)

                Request.redirect(req, *args, **kwords)
            
            assert repr(req.redirect).startswith('<bound method')
            req.redirect = my_redirect
            
        return handler
        
    def post_process_request(self, req, template, content_type):
        #if req.path_info.startswith('/login'):
        #    if 'trac_auth' in req.outcookie:
        #        req.outcookie['trac_auth']['path'] = self.uri_root
        return (template, content_type)

    # Internal methods
    def _my_redirect_back(self, req):
        """Modified version of LoginModule._redirect_back that checks 
        to see if the target is in the tracforge URI."""
        self.log.debug('TracForgeCookieMunger: In evil redirect captor')
        referer = req.get_header('Referer')
        parts = urlsplit(referer)
        if referer and (not parts[2].startswith(self.uri_root) or not parts[1].startswith(req.server_name)):
            referer = None
        req.redirect(referer or req.abs_href())

    def _my_get_header(self, name):
        """Severe evil. Contact Noah Kantrowitz if you need to know what this does."""
        if name == 'Referer':
            try:
                stack = inspect.stack()
                for s in stack:
                    if 'redirect' in s[3]:
                        pass                        
                        
            finally:
                del stack
        
        return TracForgeCookieMunger.real_get_header(self, name)
