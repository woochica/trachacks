# Authentication crosslink module
# Copyright 2006 Noah Kantrowitz

from trac.core import *
from trac.config import Option
from trac.web.auth import LoginModule
from trac.env import Environment
from trac.web.href import Href
from trac.util.html import escape, html

class TracForgeLoginModule(LoginModule):
    """Replacement for LoginModule to slave to another environment."""
    
    master_path = Option('tracforge', 'master_path',
                         doc='Path to master Trac')

    master_env = property(lambda self: Environment(self.master_path))
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
