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

# PFIE modules
from pfieModules import PlanetForgeExport

class PlanetForgeImportExportPlugin(Component):
    implements(IAdminCommandProvider, IAdminPanelProvider, ITemplateProvider)

    # CLI part (trac-admin /path/to/trac planetforge [import|export|report] ...)

    def get_admin_commands(self):
        yield ('planetforge report', '', 'Report exportable items (size, quantity)', None, PlanetForgeExport(self.env).cli_report) # safe a component is a singleton
        yield ('planetforge export', '', 'Export all Trac items in "PlanetForge" format', None, PlanetForgeExport(self.env)._cli_export)


    # WEB part (/admin/planetforge/export)

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    def get_htdocs_dirs(self):
        return []

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('planetforge', 'PlanetForge', 'export', 'Export')

    def render_admin_panel(self, req, category, page, path_info):
        print "\t INNNNNNNNNNNNNNNNNNNNNNNNNNN"
        req.perm.require('TRAC_ADMIN')
        res = {'action' : 'report'}
        action = req.args.get('action', '')
        print "\t action : ", action
        if action == 'export' :
            ticket = req.args.get('ticket', '').strip() == 'on'
            wiki = req.args.get('wiki', '').strip() == 'on' 
            revision = req.args.get('revision', '').strip() == 'on' 
            ticket_change = req.args.get('ticket_change', '').strip() == 'on'
            res = PlanetForgeExport(self.env).web_export(req)
        else :
            res = PlanetForgeExport(self.env).web_report(req)
        return './export.html', res



