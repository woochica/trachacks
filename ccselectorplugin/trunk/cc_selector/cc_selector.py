# -*- coding: utf-8 -*-

import re
import trac

from pkg_resources   import resource_filename

from trac.config     import BoolOption, Option
from trac.core       import *
from trac.perm       import PermissionSystem
from trac.web.api    import IRequestFilter, IRequestHandler
from trac.web.chrome import add_script, ITemplateProvider

# Import i18n methods.  Fallback modules maintain compatibility to Trac 0.11
# by keeping Babel optional here.
try:
    from trac.util.translation  import domain_functions
    add_domain, _ = \
        domain_functions('cc_selector', ('add_domain', '_'))
except ImportError:
    from trac.util.translation  import gettext
    _ = gettext
    def add_domain(a,b,c=None):
        pass


class TicketWebUiAddon(Component):
    implements(IRequestFilter, ITemplateProvider, IRequestHandler)

    show_fullname = BoolOption(
        'cc_selector', 'show_fullname', False,
        doc="Display full names instead of usernames if available.")
    username_blacklist = Option(
        'cc_selector', 'username_blacklist', '',
        doc="Usernames separated by comma, that should never get listed.")

    def __init__(self):
        # bind the 'cc_selector' catalog to the specified locale directory
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if re.search('ticket', req.path_info):
            add_script(req, 'cc_selector/cc_selector.js')
            if req.locale is not None:
                add_script(req, 'cc_selector/lang_js/%s.js' % req.locale)
        return(template, data, content_type)

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('cc_selector', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        return [resource_filename(__name__, 'templates')]

    # IRequestHandler
    def match_request(self, req):
        match = re.match(r'^/cc_selector', req.path_info)
        if not match is None:
            return True
        return False

    def process_request(self, req):
        add_script(req, 'cc_selector/cc_selector.js')

        blacklist = self.username_blacklist.split(', ')
        privileged_users = PermissionSystem(
            self.env).get_users_with_permission('TICKET_VIEW')
        all_users = self.env.get_known_users()

        developers = filter(lambda u: u[0] in privileged_users, all_users)
        cc_developers = filter(lambda u: not u[0] in blacklist, developers)
        # TRANSLATOR: text added per list item in popup window like
        #   [_] CC to username
        cc_to =  _("Cc to")
        data = {
            'cc_developers': cc_developers,
            'cc_to': cc_to,
            'show_fullname': self.show_fullname
            }
        return 'cc_selector.html', data, None
