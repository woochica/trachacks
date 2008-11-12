# -*- coding: utf-8 -*-
"""
    Highlight stuff using pygments
"""
import re
from trac.core import *
from trac.web import HTTPNotFound
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.config import Option
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_stylesheet, add_link
from trac.web.main import IRequestHandler
from trac.util.datefmt import http_date
from trac.util.html import html, Markup
from trac.mimeview.pygments import get_all_lexers
from trac.db import Table, Column, Index
from tracpaste.model import Paste, get_recent_pastes


class TracpastePlugin(Component):
    implements(INavigationContributor, ITemplateProvider, IRequestHandler, \
               IPermissionRequestor, IEnvironmentSetupParticipant)

    _url_re = re.compile(r'^/pastebin(?:/(\d+))?/?$')

    SCHEMA = [
        Table('pastes', key='id')[
            Column('id', auto_increment=True),
            Column('title'),
            Column('author'),
            Column('mimetype'),
            Column('data'),
            Column('time', type='int')
        ]
    ]

    # IEnvironmentSetupParticipant
    def environment_created(self):
        self._upgrade_db(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute('select count(*) from pastes')
            cursor.fetchone()
            return False
        except:
            db.rollback()
            return True

    def upgrade_environment(self, db):
        self._upgrade_db(db)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'pastebin'

    def get_navigation_items(self, req):
        if req.perm.has_permission('PASTEBIN_USE'):
            yield 'mainnav', 'pastebin', html.A('Pastebin', href=req.href.pastebin())

    # IPermissionHandler methods
    def get_permission_actions(self):
        return ['PASTEBIN_USE']

    # IRequestHandler methods
    def match_request(self, req):
        m = self._url_re.search(req.path_info)
        if m is None:
            return False
        paste_id = m.group(1)
        if paste_id:
            req.args['paste_id'] = int(paste_id)
            req.args['new_paste'] = False
        else:
            req.args['paste_id'] = None
            req.args['new_paste'] = True
        return True

    def process_request(self, req):
        req.perm.assert_permission('PASTEBIN_USE')
        add_stylesheet(req, 'pastebin/style.css')
        add_stylesheet(req, 'common/css/code.css')

        # new post
        if req.args['new_paste']:
            title = req.args.get('title', 'untitled')
            author = req.args.get('author', req.authname)
            mimetype = req.args.get('mimetype', 'text/plain')
            data = req.args.get('data', '')
            error = False

            # check if we reply to a paste
            if 'reply' in req.args and req.args['reply'].isdigit():
                paste = Paste(self.env, req.args['reply'])
                if paste:
                    title = paste.title
                    if not title.startswith('Re:'):
                        title = 'Re: ' + title
                    data = paste.data

            if req.method == 'POST':
                if not data.strip():
                    error = True
                else:
                    paste = Paste(self.env,
                        title=title,
                        author=author,
                        mimetype=mimetype,
                        data=data
                    )
                    paste.save()
                    req.redirect(req.href.pastebin(paste.id))

            data = {
                'mode':             'new',
                'mimetypes':        self._get_mimetypes(),
                'mimetype':         mimetype,
                'title':            title,
                'author':           author,
                'error':            error,
                'data':             data,
                'recent':           get_recent_pastes(self.env, 10)
            }

        # show post
        else:
            paste = Paste(self.env, req.args['paste_id'])
            if not paste:
                raise HTTPNotFound('Paste %d does not exist' %
                                   req.args['paste_id'])

            # text format
            if req.args.get('format') in ('txt', 'raw'):
                if req.args['format'] == 'txt':
                    mimetype = 'text/plain'
                else:
                    mimetype = paste.mimetype
                req.send_response(200)
                req.send_header('Content-Type', mimetype)
                req.send_header('Content-Length', len(paste.data))
                req.send_header('Last-Modified', http_date(paste.time))
                req.end_headers()
                req.write(paste.data)
                return

            data = {
                'mode':             'show',
                'paste':            paste,
            }

            # add link for text format
            raw_href = req.href.pastebin(paste.id, format='raw')
            add_link(req, 'alternate', raw_href, 'Original Format', paste.mimetype)

            if paste.mimetype != 'text/plain':
                plain_href = req.href.pastebin(paste.id, format='txt')
                add_link(req, 'alternate', plain_href, 'Plain Text', 'text/plain')

        return 'pastebin.html', data, None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('pastebin', resource_filename(__name__, 'htdocs'))]

    # private methods
    def _get_mimetypes(self):
        result = []
        for name, _, _, mimetypes in get_all_lexers():
            if mimetypes:
                result.append((mimetypes[0], name))
        result.sort(lambda a, b: cmp(a[1].lower(), b[1].lower()))
        return result

    def _upgrade_db(self, db):
        try:
            try:
                from trac.db import DatabaseManager
                db_backend, _ = DatabaseManager(self.env)._get_connector()
            except ImportError:
                db_backend = self.env.get_db_cnx()

            cursor = db.cursor()
            for table in self.SCHEMA:
                for stmt in db_backend.to_sql(table):
                    self.env.log.debug(stmt)
                    cursor.execute(stmt)
            db.commit()
        except Exception, e:
            db.rollback()
            self.env.log.error(e, exc_info=1)
            raise TracError(str(e))
