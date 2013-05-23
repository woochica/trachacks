# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Yoshiyuki Sugimoto <s.yosiyuki@gmail.com>
# Copyright (C) 2012-2013 Jun Omae <jun66j5@gmail.com>
# Copyright (C) 2012-2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
from fnmatch import fnmatchcase

from genshi.builder import tag
from trac.config import ListOption
from trac.core import Component, implements
from trac.db import Column, DatabaseManager, Table
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor, PermissionError
from trac.resource import (
    Resource, ResourceNotFound, get_resource_description,
    get_resource_name, get_resource_shortname, get_resource_summary,
)
from trac.util import get_reporter_id
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import (
    ITemplateProvider, add_ctxtnav, add_notice, add_script, add_stylesheet
)
try:
    from trac.web.api import arg_list_to_args, parse_arg_list
except ImportError:
    from compat import arg_list_to_args, parse_arg_list
try:
    from trac.resource import resource_exists  # Trac > 0.11.7
except ImportError:
    from compat import resource_exists


class BookmarkSystem(Component):
    """Bookmark Trac resources."""

    implements(ITemplateProvider, IRequestFilter, IRequestHandler,
               IEnvironmentSetupParticipant, IPermissionRequestor)

    bookmarkable_paths = ListOption('bookmark', 'paths', '/*',
        doc='List of URL paths to allow bookmarking on. Globs are supported.')

    schema = [
        Table('bookmarks', key=('resource', 'name', 'username'))[
            Column('resource'), Column('name'), Column('username'), ]
        ]

    bookmark_path = re.compile(r'/bookmark')
    path_match = re.compile(r'/bookmark/(add|delete|delete_in_page)/(.*)')
    nonbookmarkable_actions = ('copy', 'delete', 'edit', 'new', 'rename')

    ### public methods

    def get_bookmarks(self, req):
        """Return the current users bookmarks."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(
            "SELECT resource, name, username FROM bookmarks WHERE username=%s",
            (get_reporter_id(req),))
        for row in cursor:
            yield row

    def get_bookmark(self, req, resource):
        """Return the current users bookmark for a resource."""
#        resource = self.normalise_resource(resource)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT resource FROM bookmarks WHERE username=%s '
                       'AND resource = %s', (get_reporter_id(req), resource))
        row = cursor.fetchone()
        return (row and row[0])

    def set_bookmark(self, req, resource):
        """Bookmark a resource."""
#        resource = self.normalise_resource(resource)
        if self.get_bookmark(req, resource):
            return

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO bookmarks (resource,name,username) VALUES (%s,%s,%s)",
            (resource, '', get_reporter_id(req)))
        db.commit()

    def delete_bookmark(self, req, resource):
        """Bookmark a resource."""
#        resource = self.normalise_resource(resource)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('DELETE FROM bookmarks WHERE resource = %s AND username = %s',
                       (resource, get_reporter_id(req)))
        db.commit()

    # IPermissionRequestor method
    def get_permission_actions(self):
        return ['BOOKMARK_VIEW', 'BOOKMARK_MODIFY']

    ### ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('bookmark', resource_filename(__name__, 'htdocs'))]

    ### IRequestHandler methods

    def match_request(self, req):
        return self._authorize(req) and self.bookmark_path.match(req.path_info)

    def process_request(self, req):
        if not self._authorize(req):
            raise PermissionError('BOOKMARK_VIEW')
        match = self.path_match.match(self._get_resource_uri(req))

        if match:
            action, resource = match.groups()
            resource = "/" + resource

            # add bookmark
            if action == 'add':
                self.set_bookmark(req, resource)

                if self._is_ajax(req):
                    content = '&'.join((
                        'on',
                        req.href.bookmark('delete', resource),
                        'Delete bookmark'))
                    if isinstance(content, unicode):
                        content = content.encode('utf-8')
                    req.send(content)

                req.redirect(resource)

            # delete bookmark
            elif action == 'delete' or action == 'delete_in_page':
                self.delete_bookmark(req, resource)

                if action == 'delete_in_page':
                    add_notice(req, 'Bookmark is deleted.')
                    req.redirect(req.href.bookmark())

                if self._is_ajax(req):
                    content = '&'.join((
                        'off',
                        req.href.bookmark('add', resource),
                        'Bookmark this page'))
                    if isinstance(content, unicode):
                        content = content.encode('utf-8')
                    req.send(content)

                req.redirect(resource)

        # listing bookmarks
        if self._is_ajax(req):
            menu = self._get_bookmarks_menu(req)
            content = tag(tag.a('Bookmarks', href=req.href.bookmark()), menu)
            req.send(unicode(content).encode('utf-8'))

        bookmarks = [self._format_name(req, url)
                     for url, name, username in self.get_bookmarks(req)]
        return 'bookmark_list.html', {'bookmarks': bookmarks}, None

    ### IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        # Show bookmarks context menu except when on the bookmark page
        if self._authorize(req) and not self.match_request(req):
            for path in self.bookmarkable_paths:
                if fnmatchcase(req.path_info, path):
                    self.render_bookmarker(req)
                    break
        return template, data, content_type

    ### IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("select count(*) FROM bookmarks")
            cursor.fetchone()
            return False
        except:
            cursor.connection.rollback()
            return True

    def upgrade_environment(self, db):
        db_backend, _ = DatabaseManager(self.env)._get_connector()
        cursor = db.cursor()
        for table in self.schema:
            for stmt in db_backend.to_sql(table):
                self.env.log.debug(stmt)
                cursor.execute(stmt)
        db.commit()

    ### internal methods

    def _format_name(self, req, url):
        linkname = url
        name = ""
        missing = False

        path_info = url
        query_string = ''
        idx = path_info.find('?')
        if idx >= 0:
            path_info, query_string = path_info[:idx], path_info[idx:]
        href = req.href(path_info) + query_string

        args = arg_list_to_args(parse_arg_list(query_string.lstrip('?')))
        version = args.get('version', False)

        path = path_info.strip('/').split('/')
        realm = path[0]
        class_ = realm
        if len(path) > 1:
            resource = Resource(realm, path[1])
            if resource:
                if realm == 'ticket':
                    linkname = get_resource_shortname(self.env, resource)
                    try:
                        name = get_resource_summary(self.env, resource)
                    except ResourceNotFound:
                        missing = True
                    else:
                        from trac.ticket.model import Ticket
                        class_ = Ticket(self.env, resource.id)['status'] + \
                            ' ' + class_
                elif realm == 'milestone':
                    linkname = get_resource_name(self.env, resource)
                elif realm == 'wiki':
                    resource = Resource(realm, '/'.join(path[1:]), version)
                    linkname = get_resource_shortname(self.env, resource)
                    if version:
                        linkname += '@' + version
                elif realm == 'report':
                    linkname = "{%s}" % path[1]
                    name = self._format_report_name(path[1])
                elif realm == 'changeset':
                    rev = path[1]
                    parent = Resource('source', '/'.join(path[2:]))
                    resource = Resource(realm, rev, False, parent)
                    linkname = "[%s]" % rev
                    name = get_resource_description(self.env, resource)
                elif realm == 'browser':
                    parent = Resource('source', path[1])
                    resource = Resource('source', '/'.join(path[2:]), False, parent)
                    linkname = get_resource_description(self.env, resource)
                    name = get_resource_summary(self.env, resource)
                elif realm == 'attachment':
                    # Assume a file and check existence
                    parent = Resource(path[1], '/'.join(path[2:-1]))
                    resource = Resource(realm, path[-1], parent=parent)
                    linkname = get_resource_name(self.env, resource)
                    if not resource_exists(self.env, resource):
                        # Assume an attachment list page and check existence
                        parent = Resource(path[1], '/'.join(path[2:]))
                        if resource_exists(self.env, parent):
                            resource = Resource(realm, parent=parent)
                            linkname = get_resource_name(self.env, resource)
                            if not query_string:
                                # Trailing slash needed for Trac < 1.0, t:#10280
                                href += '/'
                        else:
                            # Assume it's a missing attachment
                            missing = True
                else:
                    linkname = get_resource_shortname(self.env, resource)
                    name = get_resource_summary(self.env, resource)
        elif len(path) == 1 and path[0] and path[0] != 'wiki':
            linkname = path[0].capitalize()
        else:
            class_ = 'wiki'
            linkname = 'WikiStart'

        if missing:
            href = None
            class_ = 'missing ' + realm

        return {
            'class_': class_,
            'href': href,
            'linkname': linkname,
            'name': name,
            'delete': req.href.bookmark('delete_in_page', url),
        }

    def _format_report_name(self, id):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT id, title from report WHERE id=%s', (id,))
        row = cursor.fetchone()
        if row:
            return row[1]
        else:
            return ''

    def render_bookmarker(self, req):
        if 'action' in req.args and \
                req.args['action'] in self.nonbookmarkable_actions:
            return

        resource = self._get_resource_uri(req)
        bookmark = self.get_bookmark(req, resource)

        if bookmark:
            class_ = 'bookmark_on'
            title = 'Delete Bookmark'
            href = req.href.bookmark('delete', resource)
        else:
            class_ = 'bookmark_off'
            title = 'Bookmark this page'
            href = req.href.bookmark('add', resource)
        anchor = tag.a(u'\u200b', id='bookmark_this', class_=class_,
                       title=title, href=href, data_list=req.href.bookmark())
        req.chrome.setdefault('ctxtnav', []).insert(0, anchor)

        add_script(req, 'bookmark/js/tracbookmark.js')
        add_stylesheet(req, 'bookmark/css/tracbookmark.css')

        menu = self._get_bookmarks_menu(req)
        item = tag.span(tag.a('Bookmarks', href=req.href.bookmark()),
                        menu, id='bookmark_menu')
        add_ctxtnav(req, item)

    def _get_bookmarks_menu(self, req):
        menu = tag.ul()
        for url, name, username in self.get_bookmarks(req):
            params = self._format_name(req, url)
            if params['name']:
                label = '%s %s' % (params['linkname'], params['name'])
            else:
                label = params['linkname']
            if params['href'] is not None:
                anchor = tag.a(label, href=params['href'], title=label)
                menu.append(tag.li(anchor))
        return menu

    def _get_resource_uri(self, req):
        if req.environ.get('QUERY_STRING'):
            return "?".join([req.path_info, req.environ.get('QUERY_STRING')])
        else:
            # Stripping trailing slash is needed for attachment pages t:#10280
            return req.path_info.rstrip('/')

    def _is_ajax(self, req):
        return req.get_header('X-Requested-With') == 'XMLHttpRequest'

    def _authorize(self, req):
        return req.authname != 'anonymous' and 'BOOKMARK_VIEW' in req.perm
