# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2003-2005 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2004-2005 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Jonas Borgström <jonas@edgewall.com>
#         Christopher Lenz <cmlenz@gmx.de>

from __future__ import generators
import time
import re

from trac import mimeview, util
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.Search import query_to_sql, shorten_result
from trac.Timeline import ITimelineEventProvider
from trac.versioncontrol import Changeset, Node
from trac.versioncontrol.svn_authz import SubversionAuthorizer
from trac.versioncontrol.diff import get_diff_options, hdf_diff, unified_diff
from trac.web import IRequestHandler
from trac.web.chrome import add_link, add_stylesheet, INavigationContributor, ITemplateProvider
from trac.wiki import wiki_to_html, wiki_to_oneliner, IWikiSyntaxProvider
from trac.ticket import Ticket
from trac.web.main import IRequestHandler
from trac.util import escape, Markup

class SetChangesetModule(Component):

    implements(INavigationContributor, IPermissionRequestor, IRequestHandler,
               ITimelineEventProvider, IWikiSyntaxProvider, ITemplateProvider) 

# need to add IRequestFilter when we upgrade

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'browser'

    def get_navigation_items(self, req):
        return []

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['CHANGESET_VIEW']

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/setchangeset/([0-9]+)$', req.path_info)
        if match:
            req.args['ticket_id'] = match.group(1)
            return 1

    def process_request(self, req, db=None):
        req.perm.assert_permission('CHANGESET_VIEW')

        if not db:
            db = self.env.get_db_cnx()

        # Fetch the standard ticket fields
        cursor = db.cursor()

        ticket_id = req.args.get('ticket_id')
	req.hdf['ticket_id'] = ticket_id

        repos = self.env.get_repository(req.authname)
        authzperm = SubversionAuthorizer(self.env, req.authname)

        diff_options = get_diff_options(req)
        if req.args.has_key('update'):
            req.redirect(self.env.href.setchangeset(ticket_id))

	ticket = Ticket(self.env, ticket_id)

	ticket.setchangesets = self.get_setchangesets(ticket_id,db)

	ticket.values['setchangesets'] = ticket.setchangesets

	ticket.values['changesets'] = ""
	for changeset in ticket.setchangesets:
	    ticket.values['changesets'] +=  str(changeset)
	
	setchangesets = ticket.setchangesets
	req.hdf['ticket'] = ticket
	req.hdf['dbWarning'] = False

	# get the list of changesets for the ticket_id
	# then loop through and get the actual changesets like the following line
	chgset = []
	self.log.debug('PublishRevert: %s', ticket['ticketaction'])
	for rev in setchangesets:
	    authzperm.assert_permission_for_changeset(rev)
	    changeset = repos.get_changeset(rev)
            chgset.append(changeset)

        format = req.args.get('format')

        self._render_html(req, ticket, repos, chgset, diff_options)

        return 'setchangeset.cs', None

    # ITimelineEventProvider methods

    def get_setchangesets(self, ticket_id, db=None):
        if not db:
            db = self.env.get_db_cnx()

        # Fetch the standard ticket fields
        cursor = db.cursor()

	cursor.execute("SELECT rev FROM ticket_revision WHERE ticket_id=%s",
			(ticket_id,))
	setchangesets = []
	for rev in cursor:
	    setchangesets.append(rev[0])
	return setchangesets

    def get_timeline_filters(self, req):
        if req.perm.has_permission('CHANGESET_VIEW'):
            yield ('changeset', 'Repository checkins')

    def get_timeline_events(self, req, start, stop, filters):
        if 'changeset' in filters:
            format = req.args.get('format')
            show_files = int(self.config.get('timeline',
                                             'changeset_show_files'))
            db = self.env.get_db_cnx()
            repos = self.env.get_repository()
            authzperm = SubversionAuthorizer(self.env, req.authname)
            rev = repos.youngest_rev
            while rev:
                if not authzperm.has_permission_for_changeset(rev):
                    rev = repos.previous_rev(rev)
                    continue

                chgset = repos.get_changeset(rev)
                if chgset.date < start:
                    return
                if chgset.date < stop:
                    message = chgset.message or '--'
                    if format == 'rss':
                        title = util.Markup('Changeset <em>[%s]</em>: %s',
                                            chgset.rev,
                                            util.shorten_line(message))
                        href = self.env.abs_href.changeset(chgset.rev)
                        message = wiki_to_html(message, self.env, req, db,
                                               absurls=True)
                    else:
                        title = util.Markup('Changeset <em>[%s]</em> by %s',
                                            chgset.rev, chgset.author)
                        href = self.env.href.changeset(chgset.rev)
                        message = wiki_to_oneliner(message, self.env, db,
                                                   shorten=True)
                    if show_files:
                        files = []
                        for chg in chgset.get_changes():
                            if show_files > 0 and len(files) >= show_files:
                                files.append('...')
                                break
                            files.append('<span class="%s">%s</span>'
                                         % (chg[2], util.escape(chg[0])))
                        message = '<span class="changes">' + ', '.join(files) +\
                                  '</span>: ' + message
                    yield 'changeset', href, title, chgset.date, chgset.author,\
                          util.Markup(message)
                rev = repos.previous_rev(rev)

    # Internal methods

    def _render_html(self, req, ticket, repos, chgset, diff_options):
        """HTML version"""
        req.hdf['title'] = '#%s' % ticket.id
        req.hdf['ticket'] = ticket.values
	filepaths = []
        edits = []
        idx = 0

	for changeset in chgset[::-1]:

            for path, kind, change, base_path, base_rev in changeset.get_changes():
               info = {'change': change}
               if base_path:
                   info['path.old'] = base_path
                   info['rev.old'] = base_rev
                   info['browser_href.old'] = self.env.href.browser(base_path,
                                                                    rev=base_rev)
               if path:
                   info['path.new'] = path
                   info['rev.new'] = changeset.rev
                   info['browser_href.new'] = self.env.href.browser(path,
                                                                    rev=changeset.rev)
               if change in (Changeset.COPY, Changeset.EDIT, Changeset.MOVE):
                   edits.append((idx, path, kind, base_path, base_rev))

	       if self.use_file(info, filepaths):
		       filepaths.append(info)

	       hidden_properties = [p.strip() for p
                             in self.config.get('browser', 'hide_properties').split(',')]
	
	filepaths.reverse()
	for info in filepaths:
            req.hdf['setchangeset.changes.%d' % idx] = info
	    if(info['path.new'] == 'trunk/db/database_modifications.sql'):
	    	req.hdf['dbWarning'] = "True"
	    idx += 1
		
    def use_file(self, newchange, filepaths):
	for path in filepaths:
            if path['path.new'] == newchange['path.new']:
                    return False
	return True

    def _render_diff(self, req, repos, chgset, diff_options):
        """Raw Unified Diff version"""
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain;charset=utf-8')
        req.send_header('Content-Disposition', 'inline;'
                        'filename=Changeset%s.diff' % chgset.rev)
        req.end_headers()

        for path, kind, change, base_path, base_rev in chgset.get_changes():
            if change == Changeset.ADD:
                old_node = None
            else:
                old_node = repos.get_node(base_path or path, base_rev)
            if change == Changeset.DELETE:
                new_node = None
            else:
                new_node = repos.get_node(path, chgset.rev)

            # TODO: Property changes

            # Content changes
            if kind == 'dir':
                continue

            default_charset = self.config.get('trac', 'default_charset')
            new_content = old_content = ''
            new_node_info = old_node_info = ('','')

            if old_node:
                charset = mimeview.get_charset(old_node.content_type) or \
                          default_charset
                old_content = util.to_utf8(old_node.get_content().read(),
                                           charset)
                old_node_info = (old_node.path, old_node.rev)
            if mimeview.is_binary(old_content):
                continue

            if new_node:
                charset = mimeview.get_charset(new_node.content_type) or \
                          default_charset
                new_content = util.to_utf8(new_node.get_content().read(),
                                           charset)
                new_node_info = (new_node.path, new_node.rev)
            if mimeview.is_binary(new_content):
                continue

            if old_content != new_content:
                context = 3
                for option in diff_options[1]:
                    if option.startswith('-U'):
                        context = int(option[2:])
                        break
                req.write('Index: ' + path + util.CRLF)
                req.write('=' * 67 + util.CRLF)
                req.write('--- %s (revision %s)' % old_node_info +
                          util.CRLF)
                req.write('+++ %s (revision %s)' % new_node_info +
                          util.CRLF)
                for line in unified_diff(old_content.splitlines(),
                                         new_content.splitlines(), context,
                                         ignore_blank_lines='-B' in diff_options[1],
                                         ignore_case='-i' in diff_options[1],
                                         ignore_space_changes='-b' in diff_options[1]):
                    req.write(line + util.CRLF)

    def _render_zip(self, req, repos, chgset):
        """ZIP archive with all the added and/or modified files."""
        req.send_response(200)
        req.send_header('Content-Type', 'application/zip')
        req.send_header('Content-Disposition', 'attachment;'
                        'filename=Changeset%s.zip' % chgset.rev)
        req.end_headers()

        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

        buf = StringIO()
        zipfile = ZipFile(buf, 'w', ZIP_DEFLATED)
        for path, kind, change, base_path, base_rev in chgset.get_changes():
            if kind == Node.FILE and change != Changeset.DELETE:
                node = repos.get_node(path, chgset.rev)
                zipinfo = ZipInfo()
                zipinfo.filename = node.path
                zipinfo.date_time = time.gmtime(node.last_modified)[:6]
                zipinfo.compress_type = ZIP_DEFLATED
                zipfile.writestr(zipinfo, node.get_content().read())
        zipfile.close()
        req.write(buf.getvalue())

    # IWikiSyntaxProvider methods
    
    def get_wiki_syntax(self):
        yield (r"!?\[\d+\]|(?:\b|!)r\d+\b(?!:\d)",
               lambda x, y, z: self._format_link(x, 'changeset',
                                                 y[0] == 'r' and y[1:]
                                                 or y[1:-1], y))

    def get_link_resolvers(self):
        yield ('changeset', self._format_link)

    def _format_link(self, formatter, ns, rev, label):
        cursor = formatter.db.cursor()
        cursor.execute('SELECT message FROM revision WHERE rev=%s', (rev,))
        row = cursor.fetchone()
        if row:
            return '<a class="changeset" title="%s" href="%s">%s</a>' \
                   % (util.escape(util.shorten_line(row[0])),
                      formatter.href.changeset(rev), label)
        else:
            return '<a class="missing changeset" href="%s" rel="nofollow">%s</a>' \
                   % (formatter.href.changeset(rev), label)


    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    def save_changesets(self, ticket_id, author, rev, when=0):
        """
        Store ticket setchangesets in the database. The ticket must already exist in
        the database.
        """
	
	# TODO: fetch ticket and assert it exists
	ticket = Ticket(self.env, ticket_id)
        assert ticket.exists, 'Cannot update a new ticket'
	db = None
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
        cursor = db.cursor()
        when = int(when or time.time())

        cursor.execute("INSERT INTO ticket_revision (rev,ticket_id) VALUES(%s,%s)",
                       (rev, ticket_id))
        if handle_ta:
            db.commit()

        ticket._old = {}
        ticket.time_changed = when

    def post_process_request(self, req, template, content_type):
        match = re.match(r'/ticket/([0-9]+)$', req.path_info)
        if match:
            req.hdf['ticket.setchangeset'] = Markup('<a href="...">...</a>')
