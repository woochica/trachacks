# -*- coding: utf-8 -*-

from __future__ import generators

# General includes
import time

# Track includes
from trac.core import *
from trac.db import *
from trac.web import IRequestHandler
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
  add_stylesheet
from trac.perm import IPermissionRequestor
from trac.util import Markup, format_datetime

# Local includes
from guestbook.db import version, schema

"""
  Guestbook plugin for Trac. Allows to get some feedback from anonymous users
  even if Trac's Wiki is read-only.
"""
class GuestbookPlugin(Component):

    #
    # Public methods
    #

    implements(IEnvironmentSetupParticipant, IPermissionRequestor,
      INavigationContributor, ITemplateProvider, IRequestHandler)

    # IEnvironmentSetupParticipant

    """

    """
    def environment_created(self):
        pass

    """
      Determines if database is of same version as is version of this plugin.
    """
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT value FROM system WHERE name='guestbook_version'")
            for row in cursor:
                return int(row[0]) != version
            return True
        except:
            return True

    """
      Creates or upgrades database to current version.
    """
    def upgrade_environment(self, db):
        cursor = db.cursor()
        for table in schema:
            queries = db.to_sql(table)
            for query in queries:
                cursor.execute(query)
        cursor.execute("INSERT INTO system VALUES ('guestbook_version', %s)",
          [version])
        #except:
          #cursor.execute("UPDATE system SET value = %i WHERE name = 'discussion_version'", discussion_version)

    # IPermissionRequestor methods

    """
      Returns list of permitions privided by this plugin.
    """
    def get_permission_actions(self):
        return ['GUESTBOOK_VIEW', 'GUESTBOOK_APPEND', 'GUESTBOOK_DELETE']

    # ITemplateProvider methods

    """
      Returns additional path where stylesheets are placed.
    """
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('guestbook', resource_filename(__name__, 'htdocs'))]

    """
      Returns additional path where templates are placed.
    """
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods

    """
      Returns name of active navigation item.
    """
    def get_active_navigation_item(self, req):
        return 'guestbook'

    """
      Returns navigation items provided by this plugin.
    """
    def get_navigation_items(self, req):
        if not req.perm.has_permission('GUESTBOOK_VIEW'):
            return
        yield 'mainnav', 'guestbook', Markup('<a href="%s">%s</a>' % \
          (self.env.href.guestbook(), self.env.config.get('guestbook',
          'title', 'Guestbook')))

    # IRequestHandler methods

    """
      Determines if request should be handled by this plugin.
    """
    def match_request(self, req):
        if req.path_info == '/guestbook':
            return True
        else:
            return False

    """
      Handles display, append and delete requests on this plugin.
    """
    def process_request(self, req):
        req.perm.assert_permission('GUESTBOOK_VIEW')

        # getting cursor
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if req.args.has_key('action'):
            # process append request
            if req.args['action'] == 'newentry':
                req.perm.assert_permission('GUESTBOOK_APPEND')
                self._append_message(cursor, req.args['author'],
                  req.args['title'], req.args['text'])
            # process delete request
            if req.args['action'] == 'delete':
                req.perm.assert_permission('GUESTBOOK_DELETE')
                self._delete_message(cursor, req.args['id'])

        # adding stylesheets
        add_stylesheet(req, 'common/css/default.css')
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'guestbook/css/guestbook.css')

        # passing variables to template
        req.hdf['guestbook.title'] = self.env.config.get('guestbook',
          'title', 'Guestbook')
        req.hdf['guestbook.messages'] = self._get_messages(req, cursor)
        req.hdf['guestbook.append'] = req.perm.has_permission('GUESTBOOK_VIEW');

        # database commit and return page content
        db.commit()
        return 'guestbook.cs', 'text/html'

    #
    # Private methods
    #

    """
      Returns list of messages in guestbook.
    """
    def _get_messages(self, req, cursor):
        cursor.execute("SELECT id, author, time, title, body FROM guestbook"
          " ORDER BY time")
        columns = ['id', 'author', 'time', 'title', 'body']
        messages = []
        for message in cursor:
            message = dict(zip(columns, message))
            message['time'] =  format_datetime(message['time'])
            message['title'] = wiki_to_oneliner(message['title'], self.env)
            message['body'] = wiki_to_html(message['body'], self.env, req)
            messages.append(message)
        return messages

    """
      Appends a new message into guestbook.
    """
    def _append_message(self, cursor, author, title, text):
        cursor.execute("INSERT INTO guestbook (author, time, title, body)"
          " VALUES (%s, %s, %s, %s)", [author or 'anonymous', str(time.time()),
          title or 'untitled', text])

    """
      Deletes message from guestbook.
    """
    def _delete_message(self, cursor, id):
        cursor.execute("DELETE FROM guestbook WHERE id = %s", [id])
