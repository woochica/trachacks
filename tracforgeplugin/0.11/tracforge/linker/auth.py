# Authentication crosslink module
# Copyright 2006 Noah Kantrowitz

from trac.core import *
from trac.config import Option
from trac.web.auth import LoginModule
from trac.web.href import Href
from trac.env import open_environment
from trac.util.html import escape, html
from trac.web.api import IRequestFilter, Request

from urlparse import urlsplit

class TracForgeLoginModule(LoginModule):
    """Replacement for LoginModule to slave to another environment."""
    
    master_path = Option('tracforge', 'master_path',
                         doc='Path to master Trac')

    master_env = property(lambda self: open_environment(self.master_path, use_cache=True))
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
                   
    # IRequestHandler methods
    def process_request(self, req):
        if req.path_info.startswith('/login'):
            if req.authname and req.authname != 'anonymous':
                # Already logged in, reconstruct last path
                req.redirect(req.href())
            else:
                # Safe, send to master
                req.redirect(self.master_href.login())
        raise TracError

    # Internal methods
    def _get_name_for_cookie(self, req, cookie):
        return LoginModule(self.master_env)._get_name_for_cookie(req, cookie)

class TracForgeCookieMunger(Component):
    
    uri_root = Option('tracforge', 'uri_root', default='/',
                      doc='The smallest common URI for the whole TracForge setup')
                      
    implements(IRequestFilter)

    def pre_process_request(self, req, handler):
        if req.path_info.startswith('/login') or req.path_info.startswith('/logout'):
            old_redirect = req.redirect
            def my_redirect(*args, **kwords):
                # Munge the cookie path
                if 'trac_auth' in req.outcookie:
                    assert not self.uri_root.startswith('http'), 'The tracforge uri_root must be set to relative path'
                    req.outcookie['trac_auth']['path'] = self.uri_root

                # Check to see if we should refer back to sibling Trac
                referer = req.args.get('referer')
                self.log.debug('TracForgeCookieMunger: Got referer as %r'%referer)
                if referer:
                    parts = urlsplit(referer or '')
                    self.log.debug('TracForgeCookieMunger: parts=%s name=%r'%(parts,req.server_name))
                    if parts[2].startswith(self.uri_root) and (not parts[1] or parts[1] == req.server_name):
                        Request.redirect(req, referer)

                old_redirect(req, *args, **kwords)
            
            req.redirect = my_redirect
            
        return handler
        
    def post_process_request(self, req, template, content_type):
        return (template, content_type)

