# -*- coding: utf-8 -*-

from trac.core import *

from trac.util.html import html
from trac.util.text import print_table, printout, unicode_quote
from trac.util.translation import _, N_, gettext

from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, Chrome

from trac.db.api import with_transaction

from trac.admin.api import IAdminCommandProvider, IAdminPanelProvider

from trac.loader import get_plugin_info

from trac.ticket import model
from trac.ticket.model import Ticket

from trac.config import IntOption

from urlparse import urlparse
import json
import os
from zipfile import ZipFile


class PlanetForgeImport(Component):
    implements(IAdminCommandProvider, IAdminPanelProvider, ITemplateProvider)

    # Configure in .ini with [planetforge] import_max_size = (in bytes)
    max_size = IntOption('planetforge', 'import_max_size', 2**20) # 1MB

    def _dump_path(self, fname = ''):
        return os.path.join(self.env.path, 'import', fname)

    def _dump_load(self, path):
        dump = ZipFile(path, 'r')
        meta = dump.open('Plucker/JSON_Pluck.txt').read()
        dump.close()
        return json.loads(meta)

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
        res = {}
        action = req.args.get('action', '')
        fname  = req.args.get('file', '')
        if  fname != '' and action == 'import' :
            res = self.web_import(req, fname)
        elif fname != '' :
            res = self.web_preview(req, fname)
        else :
            res = self.web_upload(req)
        return './import.html', res

    def web_upload(self, req):
        # TODO: handle file upload when POSTing
        files = []
        for fname in os.listdir(self._dump_path()):
            fpath = os.path.join(self._dump_path(), fname)
            fstat = os.stat(fpath)
            files.append({
                'name': unicode_quote(fname),
                'size': fstat.st_size,
                'date': fstat.st_mtime })
        return {'max_size': self.max_size, 'files': files, 'action': 'upload'}

    def web_preview(self, req, fname):
        # TODO
        meta = self._dump_load(self._dump_path(fname))
        p = meta['project']
        roles = meta['roles'].keys()
        users = meta['users'].keys()
        trackers = [t['label'] for t in meta['trackers']]
        docnb = sum([sum([len(docs) for cat, docs in cats.iteritems()]) for status, cats in meta['docman'].iteritems()])
        infos = [
            ('Name',        p['project']),
            ('Description', p['description']),
            ('URL',         p['URL']),
            ('Roles',       '%d role(s)' % len(roles) if len(roles) else 'none'),
            ('Users',       '%d user(s)' % len(users) if len(users) else 'none'),
            ('Trackers',    '%d (%s)' % (len(trackers), ', '.join(trackers)) if len(trackers) else 'none'),
            ('Docman',      '%d document(s)' % (docnb) if docnb else 'none'),
        ]
        #dump = json.dumps(meta, sort_keys=True, indent=2)
        return {'action': 'preview', 'file': fname, 'infos': infos}

    def web_import(self, req, fname):
        meta = self._dump_load(self._dump_path(fname))
        # TODO: at least import meta['trackers'] (merge all trackers)
        return {'action': 'import', 'file': fname}

