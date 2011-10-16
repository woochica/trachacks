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
import re
import os
import datetime
import dateutil.parser
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
        for fname in sorted(os.listdir(self._dump_path())):
            fpath = os.path.join(self._dump_path(), fname)
            fstat = os.stat(fpath)
            files.append({
                'name': fname,
                'url' : unicode_quote(fname),
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
        preserve = req.authname if req.args.get('preserve') else ''
        reset    = req.args.get('reset') == 'on'
        meta     = self._dump_load(self._dump_path(fname))
        status = {
            'User and roles import' : self._import_users(meta, reset, req.authname),
            'Trackers import'       : self._import_trackers(meta, reset),
        }
        # TODO: at least import meta['trackers'] (merge all trackers)
        return {'action': 'import', 'file': fname, 'status': status}


    # This actually import _roles_ and users
    def _import_users(self, meta, reset, preserve):
        rolemap = {}
        for role, info in meta['roles'].iteritems():
            if role == '':
                continue
            if info.get('Project Admin', '') == 'Admin':
                rolemap[role] = set(['TRAC_ADMIN'])  # God mode
                continue

            perms = set()
            perms.add('WIKI_VIEW')  # Always show wiki

            if info['SCM'] != 'No access':  # Any SCM access implies browser/changeset consultation
                perms.add('BROWSER_VIEW')
                perms.add('CHANGESET_VIEW')
                perms.add('TIMELINE_VIEW')

            if info.get('Tasks Admin', '') == 'Admin':  # We'll consider a 'task admin' as a milestone admin
                perms.add('MILESTONE_ADMIN')
            else:
                perms.add('MILESTONE_VIEW')
                perms.add('REPORT_VIEW')

            tracker_admin  = len([1 for k,v in info.iteritems() if k.find('Tracker:') == 0 and re.search('Admin', v)])
            tracker_writer = len([1 for k,v in info.iteritems() if k.find('Tracker:') == 0 and re.search('Write|Tech', v)])
            tracker_reader = len([1 for k,v in info.iteritems() if k.find('Tracker:') == 0 and re.search('Read|Public', v)])
            if info.get('Tracker Admin', '') == 'Admin' or tracker_admin:
                # Tracker admin or at least admin on 1 tracker
                perms.add('TICKET_ADMIN')
                perms.add('REPORT_ADMIN')
            elif tracker_writer:
                # At least writer on 1 tracker
                perms.add('TICKET_CREATE')
                perms.add('TICKET_APPEND')
                perms.add('TICKET_VIEW')
            elif tracker_reader:
                perms.add('TICKET_VIEW')

            rolemap[role] = perms

        if reset:
            # We delete all permissions except those from the importing user as a safety net.
            # Same for session_attributes (email, name, presf, etc).
            @self.env.with_transaction()
            def do_reset_users(db):
                cursor = db.cursor()
                cursor.execute("DELETE FROM permission WHERE username<>%s", (preserve,))
                cursor.execute("DELETE FROM session_attribute WHERE sid<>%s", (preserve,))
                cursor.execute("DELETE FROM session WHERE sid<>%s", (preserve,))

        for login, info in meta['users'].iteritems():
            if login == preserve:
                continue
            role = info['role']
            perms = rolemap[role]
            @self.env.with_transaction()
            def do_config_users(db):
                cursor = db.cursor()
                for perm in perms:
                    cursor.execute("INSERT INTO permission (username, action) "
                                   "VALUES (%s, %s)", (login, perm))
                cursor.execute("INSERT INTO session (sid, authenticated, last_visit) "
                               "VALUES (%s, 1, 1)", (login,))
                cursor.execute("INSERT INTO session_attribute (sid, authenticated, name, value) "
                               "VALUES (%s, 0, 'name', %s), (%s, 1, 'email', %s)", (
                    login, info['real_name'],
                    login, info['mail'] ))

        return 'OK. Use "lost password" feature to generate new passwords.'


    # This actually import components, priorities, etc... and tickets
    def _import_trackers(self, meta, reset):
        types       = set()
        components  = set()
        priorities  = set()
        resolutions = set()
        for tracker in meta['trackers']:
            types.add(tracker['label'])
            v = tracker['vocabulary']
            for x in v.get('Category', []):
                components.add(x)
            for x in v.get('priority', []):
                priorities.add(x)
            for x in v.get('Resolution', []):
                resolutions.add(x)

        if reset:
            @self.env.with_transaction()
            def do_reset_components(db):
                cursor = db.cursor()
                cursor.execute("DELETE FROM component")
                cursor.execute("DELETE FROM milestone")
                cursor.execute("DELETE FROM enum")
                cursor.execute("DELETE FROM version")
                cursor.execute("DELETE FROM ticket")
                cursor.execute("DELETE FROM ticket_change")

        @self.env.with_transaction()
        def do_reset_ticket_meta(db):
            cursor = db.cursor()
            for x in sorted(components):
                cursor.execute("INSERT INTO component (name, owner, description) VALUES (%s, 'admin', %s)", (x, x))
            for i, x in enumerate(sorted(types)):
                cursor.execute("INSERT INTO enum (type, name, value) VALUES ('ticket_type', %s, %s)", (x, i+1))
            for i, x in enumerate(sorted(priorities)):
                cursor.execute("INSERT INTO enum (type, name, value) VALUES ('priority', %s, %s)", (x, i+1))
            for i, x in enumerate(sorted(resolutions)):
                cursor.execute("INSERT INTO enum (type, name, value) VALUES ('resolution', %s, %s)", (x, i+1))

        for tracker in meta['trackers']:
            label = tracker['label']
            for a in tracker['artifacts']:
                owner = a.get('assigned_to', '')
                if owner == 'Nobody' or owner == 'No Change':
                    owner = ''

                ticket = Ticket(self.env) #, a['id'])
                ticket.populate({
                    'summary'    : a.get('summary', ''),
                    'reporter'   : a.get('submitter', ''),
                    'description': a.get('description', ''),
                    'type'       : label,
                    'priority'   : a.get('priority', ''),
                    'component'  : a.get('Category', ''),
                    'owner'      : owner,
                    'status'     : a.get('status', ''),
                    'cc'         : '',
                    'keywords'   : '',
                })
                created = dateutil.parser.parse(a['date'])
                ticket.insert(created)

                changes = a['comments']
                changes.extend(a['history'])
                lastcom = None
                for c in sorted(changes, key=lambda x:x['date']):
                    modified = dateutil.parser.parse(c['date'])
                    if c['class'] == 'COMMENT':
                        author = c.get('submitter', '')
                        comment  = c.get('comment', '')
                        if lastcom != None and lastcom == modified:
                            modified += datetime.timedelta(0,10)
                        lastcom = modified
                    elif c['class'] == 'FIELDCHANGE':
                        author = c['by']
                        comment = None
                        field  = c['field']
                        value  = c['old']  # WTF?
                        if field == 'status':
                            ticket.status = value
                        elif field == 'Resolution':
                            ticket.resolution = value
                        elif field == 'assigned_to':
                            ticket.owner = value
                        elif field == 'close_date':
                            continue
                    ticket.save_changes(author, comment, modified)

        return 'OK'

