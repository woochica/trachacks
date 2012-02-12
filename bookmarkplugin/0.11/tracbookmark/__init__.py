import re
from trac.core import *
from trac.config import ListOption
from trac.env import IEnvironmentSetupParticipant
from trac.web.api import IRequestFilter, IRequestHandler, Href
from trac.web.chrome import ITemplateProvider, add_stylesheet, \
                            add_script, add_notice
from trac.resource import Resource, get_resource_description
from trac.db import DatabaseManager, Table, Column
from trac.perm import IPermissionRequestor
from trac.util import get_reporter_id
from genshi.builder import tag


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

    image_map = { 'on'  : 'bookmark_on.png',
                  'off' : 'bookmark_off.png', }

    ### public methods

    def get_bookmarks(self, req):
        """Return the current users bookmarks."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT resource, name, username FROM bookmarks WHERE username=%s ',
                         (get_reporter_id(req), ))
        return cursor.fetchall()

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
        cursor.execute('INSERT INTO bookmarks (resource, username) '
                       'VALUES (%s, %s)',
                       (resource, get_reporter_id(req)))
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
        return 'BOOKMARK_VIEW' in req.perm and self.bookmark_path.match(req.path_info)

    def process_request(self, req):
        req.perm.require('BOOKMARK_VIEW')
        match = self.path_match.match(self._get_resource_uri(req))

        if match:
            action, resource = match.groups()
            resource = "/" + resource

            # add bookmark
            if action == 'add':
                self.set_bookmark(req, resource)

                if self._is_ajax(req):
                    content = "&".join((req.href.chrome('bookmark/' + self.image_map['on']),
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
                    content = "&".join((req.href.chrome('bookmark/' + self.image_map['off']),
                                    req.href.bookmark('add', resource),
                                    'Bookmark this page'))

                    if isinstance(content, unicode):
                        content = content.encode('utf-8')
                    req.send(content)

                req.redirect(resource)

        base_path = req.base_path

        # listing bookmarks
        if self._is_ajax(req):
            menu = tag.ul('', id='bookmark_menu', title='')

            anc = tag.a("Bookmarks", href=req.href.bookmark())
            menu.append(tag.li(anc))

            for url, name, username in self.get_bookmarks(req):
                resource = url
                anc = tag.a(resource, href=base_path + resource)
                menu.append(tag.li(anc))

            content = "%s" % menu

            if isinstance(content, unicode):
                content = content.encode('utf-8')
            req.send(content)

        bookmarks = []
        for url, name, username in self.get_bookmarks(req):
            bookmarks.append(self.__format_name(req, url))

        return 'list.html', { 'bookmarks': bookmarks }, None

    ### IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if 'BOOKMARK_VIEW' in req.perm:
            for path in self.bookmarkable_paths:
                if re.match(path, req.path_info):
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

    def __format_name(self, req, url):
        linkname = url
        name = ""

        path = url.split('/')
        realm = path[1]
        if len(path) >= 3:
            resource = Resource(realm, path[2])
            if resource:
                if realm == 'ticket':
                    linkname = get_resource_description(self.env, resource, 'compact')
                    name = get_resource_description(self.env, resource, 'summary')
                elif realm == 'milestone':
                    linkname = get_resource_description(self.env, resource, 'compact')
                elif realm == 'wiki':
                    resource = Resource(realm, '/'.join(path[2:]))
                    linkname = get_resource_description(self.env, resource, 'compact')
                elif realm == 'report':
                    linkname = "{%s}" % path[2]
                    name = self.__format_report_name(path[2])
                elif realm == 'changeset':
                    parent = Resource('source', path[3])
                    resource = Resource(realm, path[2], False, parent)
                    linkname = "[%s]" % path[2]
                    name = get_resource_description(self.env, resource)
                elif realm == 'browser':
                    parent = Resource('source', path[2])
                    self.env.log.debug("==============================> %s" % "/".join(path[3:]))
                    resource = Resource('source', '/'.join(path[3:]), False, parent)
                    linkname = get_resource_description(self.env, resource)
                    name = get_resource_description(self.env, resource, 'summary')
                elif realm == 'attachment':
                    parent = Resource(path[2], '/'.join(path[3:-1]))
                    resource = Resource(realm, path[-1], False, parent)
                    linkname = get_resource_description(self.env, resource, 'compact')
                    name = get_resource_description(self.env, resource, 'summary')
                else:
                    linkname = get_resource_description(self.env, resource, 'compact')
                    name = get_resource_description(self.env, resource, 'summary')
        elif len(path) == 2 and path[1]:
            linkname = path[1].capitalize()
        else:
            realm = 'wiki'
            linkname = 'WikiStart'

        return {
            'realm': realm,
            'url': req.href(url),
            'linkname': linkname,
            'name': name,
            'delete': req.href.bookmark('delete_in_page', url),
        }

    def __format_report_name(self, id):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT id, title from report WHERE id=%s', (id,))
        row = cursor.fetchone()
        if row:
            return row[1]
        else:
            return ''

    def render_bookmarker(self, req):
        resource = self._get_resource_uri(req)
        bookmark = self.get_bookmark(req, resource)

        if bookmark:
            img = tag.img(src=req.href.chrome('bookmark/' + self.image_map['on']))
            anchor = tag.a(img, id='bookmark_this',
                    href=req.href.bookmark('delete', resource), title='Delete Bookmark')
        else:
            img = tag.img(src=req.href.chrome('bookmark/' + self.image_map['off']))
            anchor = tag.a(img, id='bookmark_this',
                    href=req.href.bookmark('add', resource), title='Bookmark this page')

        add_script(req, 'bookmark/js/tracbookmark.js')
        add_stylesheet(req, 'bookmark/css/tracbookmark.css')
        elm = tag.span(anchor, id='bookmark', title='')
        req.chrome.setdefault('ctxtnav', []).insert(0, elm)

        menu = tag.ul('', id='bookmark_menu', title='')

        anc = tag.a("Bookmarks", href=req.href.bookmark())
        menu.append(tag.li(anc))


        for url, name, username in self.get_bookmarks(req):
            base_path = req.base_path
            params = self.__format_name(req, url)
            if params['name']:
                name = ' '.join([params['linkname'], params['name']])
            else:
                name = params['linkname']
            anc = tag.a(name, href=base_path + url)
            menu.append(tag.li(anc))

        placeholder = tag.span(menu, id='bookmark_placeholder')
        req.chrome.setdefault('ctxtnav', []).append(placeholder)

    def _get_resource_uri(self, req):
        if req.environ.get('QUERY_STRING'):
            return "?".join([req.path_info, req.environ.get('QUERY_STRING')])
        else:
            return req.path_info

    def _is_ajax(self, req):
        return req.get_header('X-Requested-With') == 'XMLHttpRequest'
