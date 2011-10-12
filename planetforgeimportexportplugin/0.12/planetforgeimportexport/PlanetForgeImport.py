# -*- coding: utf-8 -*-

from trac.core import *

from trac.util.html import html
from trac.util.text import print_table, printout
from trac.util.translation import _, N_, gettext

from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, Chrome

from trac.db.api import with_transaction

from trac.admin.api import IAdminCommandProvider, IAdminPanelProvider

from trac.loader import get_plugin_info

from trac.ticket import model
from trac.ticket.model import Ticket

from urlparse import urlparse
import json


class PlanetForgeImport(Component):
    implements(IAdminCommandProvider, IAdminPanelProvider, ITemplateProvider)


    # CLI part (trac-admin /path/to/trac planetforge import foobar.coclico.gz)

    def get_admin_commands(self):
        yield ('planetforge import', '', 'Import project items from a "PlanetForge" compatible dump', None, self.cli_import)

    def cli_import(self) :
        print "Not implemented yet."


    # WEB part (/admin/planetforge/import)

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    def get_htdocs_dirs(self):
        return []

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('planetforge', 'PlanetForge', 'import', 'Import')

    def render_admin_panel(self, req, category, page, path_info):
        req.perm.require('TRAC_ADMIN')
        res = {'action' : 'upload'}
        action = req.args.get('action', '')
        if action == 'import' :
            # FIXME
            res = self.web_import(req)
        else : # action == 'upload'
            res = self.web_import(req)
        return './import.html', res

    def web_import(self, req):
        # TODO
        return {}

