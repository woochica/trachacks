# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2003-2005 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgstr�m <jonas@edgewall.com>
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
# Author: Jonas Borgstr�m <jonas@edgewall.com>
#         Christopher Lenz <cmlenz@gmx.de>

# from __future__ import generators
# import time
import re
import commands

from trac import mimeview, util
from trac.core import *

# the following line should be added when upgrading to the newest version of trac
# from trac.config import BoolOption, Option
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

class SVNPublishModule(Component):

    implements(INavigationContributor, IPermissionRequestor, IRequestHandler,
               ITimelineEventProvider, IWikiSyntaxProvider, ITemplateProvider)

# the folloing line will be used when we upgrade to the newest version of Trac
#    default_svn_path = Option('publishrevert', 'default_svn_path', '',
# 	        """/usr/bin""")

# the following options will be deprecated in facor of the previous lines when we upgrade Trac
    default_svn_path = "/usr/bin"
    default_test_remote_host = "clone"
#    default_prod_remote_host = "vacationrentalagent.com"
    default_ssh_path = "/usr/bin"
    default_ssh_user = "trac"
    default_htdoc_path = "/var/www/vra1"
    default_lockfile = '/var/www/vra1/trunk/www/trac_publishrevert'

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
        match = re.match(r'/svnpublish/([0-9]+)$', req.path_info)
        if match:
            req.args['ticket_id'] = match.group(1)
            return 1

    def process_request(self, req, db=None):
        req.perm.assert_permission('TRAC_ADMIN')

        if not db:
            self.db = self.env.get_db_cnx()

        ticket_id = req.args.get('ticket_id')
	req.hdf['ticket_id'] = ticket_id
	req.hdf['message'] = ''

        repos = self.env.get_repository(req.authname)
        authzperm = SubversionAuthorizer(self.env, req.authname)

        diff_options = get_diff_options(req)
        if req.args.has_key('update'):
            req.redirect(self.env.href.svnpublish(ticket_id))

	ticket = Ticket(self.env, ticket_id)
        chgset = []

	if(ticket['ticketaction'] == "ClonePublish"):
            from publishrevert.setchangeset import SetChangesetModule
  	    setchangeset = SetChangesetModule(self.env)
            setchangesets = setchangeset.get_setchangesets(ticket_id)

	    # get the list of changesets for the ticket_id
	    # then loop through and get the actual changesets like the following line
	    for rev in setchangesets:
	        authzperm.assert_permission_for_changeset(rev)
	        changeset = repos.get_changeset(rev)

	    # now loop through the files in changeset to get all the paths
	    # and for each path, find the current test/prod revision number and save that info
                chgset.append(changeset)

            format = req.args.get('format')
            self._render_html(req, ticket, repos, chgset, diff_options)
	    req.hdf['setchangesets'] = setchangesets
	    ticket['ticketaction'] = 'CloneTest'
	    ticket.save_changes(req.authname, 'published to clone', 0, db)
	    req.hdf['message'] += 'Successfully Published All Files'
            req.hdf['ticket'] = ticket.values
	else:
	    req.hdf['error'] = 'Error: not in correct state to publish'

        return 'setchangeset.cs', None

    # ITimelineEventProvider methods

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

#              if change in (Changeset.COPY, Changeset.EDIT, Changeset.MOVE):
               edits.append((idx, path, kind, base_path, base_rev))

	       if self.use_file(info, filepaths):
		       filepaths.append(info)

	       hidden_properties = [p.strip() for p
                             in self.config.get('browser', 'hide_properties').split(',')]

   # the following lines probably belong outside of this _render_html function and inside process_request instead
	self.svn_init()
	req.hdf['svn_commands'] = ''
	filepaths.reverse()
	for info in filepaths:
	    info['prod_rev'] = self.svn_rev_num(info['path.new'])
   	    revert_rev = info['prod_rev']
	    server = 1 # clone = 1, prod = 2

	    if(self.db_rev_num(server,info['path.new']) == "True"):
	       self.update_rev_num(server,info['path.new'],revert_rev,ticket.id)
	    else:
               self.insert_rev_num(server,info['path.new'],revert_rev,ticket.id)

   	    # now do the update
            if(int(info['prod_rev']) < int(info['rev.new'])):
	       req.hdf['message'] += self.svn_update(req,server,info['path.new'],info['rev.new'])

            req.hdf['setchangeset.changes.%d' % idx] = info
	    idx += 1
	self.svn_close()
	req.hdf['svn_commands'] = req.hdf['svn_commands'].split(',')

    def use_file(self, newchange, filepaths):
	for path in filepaths:
            if path['path.new'] == newchange['path.new']:
                    return False
	return True

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


    # this function just returns the current revision number of the specified filename
    def svn_rev_num(self,filename):
      # eventually use the remote svn path and the remote svn config directory specified in trac.ini

      # this command will eventually be a remote ssh command to execute
      cmd="%s/ssh %s@%s %s/svn --config-dir /home/bmcquay/.subversion/ info %s/%s" % (self.default_ssh_path, self.default_ssh_user, self.default_test_remote_host, self.default_svn_path, self.default_htdoc_path, filename)
      output = commands.getoutput(cmd)
      output = output.replace("\n", " ")
      # check if the file even exists
      parsed_output = re.search("Revision: \d+",output)
      if(parsed_output == None):
        return "-1"

      parsed_output = parsed_output.group().replace("Revision: ", "")
      return int(parsed_output.strip())


    def svn_update(self,req,server,filename,rev):
      # eventually use the remote svn path and the remote svn config directory specified in trac.ini
      if(server == 1):
         remote_host = self.default_test_remote_host
      else:
         remote_host = self.default_prod_remote_host

      # this command will eventually be a remote ssh command to execute
      cmd="%s/ssh %s@%s %s/svn --config-dir /home/%s/.subversion/ update -r %s %s/%s" % (self.default_ssh_path, self.default_ssh_user, remote_host, self.default_svn_path, self.default_ssh_user, rev, self.default_htdoc_path, filename)
      req.hdf['svn_commands'] += cmd + ','
      output = commands.getoutput(cmd)
      return output


    def db_rev_num(self, server, filename, db=None):
        if not db:
            db = self.env.get_db_cnx()

        # Fetch the standard ticket fields
        cursor = db.cursor()
	query = 'SELECT rev FROM file_revision WHERE server=%s AND file=%s'
	cursor.execute(query,(server,filename))
        row = cursor.fetchone()
	if(row == None):
	  return "False"
	else:
	  return "True"


    def update_rev_num(self, server, filename, rev, ticket_id, db=None):
        if not db:
            db = self.env.get_db_cnx()
	    commit = True
	else:
	    commit = False

        cursor = db.cursor()
	query = 'UPDATE file_revision SET rev = %s , ticket_id = %s WHERE server=%s AND file=%s'
	cursor.execute(query,(rev, ticket_id, server, filename))
	if(commit):
            db.commit()


    def insert_rev_num(self, server, filename, rev, ticket_id, db=None):
        if not db:
            db = self.env.get_db_cnx()
	    commit = True
	else:
	    commit = False

        cursor = db.cursor()
	query = 'INSERT INTO file_revision (rev,file,server,ticket_id) VALUES (%s,%s,%s,%s)'
	cursor.execute(query, (rev,filename,server,ticket_id))
	if(commit):
	    db.commit()

    def svn_init(self):
	# touch the file
	cmd="%s/ssh %s@%s touch %s" % (self.default_ssh_path, self.default_ssh_user, self.default_test_remote_host, self.default_lockfile)
	output = commands.getoutput(cmd)

    def svn_close(self):
	# delete the file
	cmd="%s/ssh %s@%s rm -f %s" % (self.default_ssh_path, self.default_ssh_user, self.default_test_remote_host, self.default_lockfile)
	output = commands.getoutput(cmd)