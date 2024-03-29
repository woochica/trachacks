# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Alec Thomas <alec@swapoff.org>
# Copyright (C) 2009 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# Copyright (C) 2013 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Alec Thomas

import re
from fnmatch import fnmatchcase

from datetime import datetime

from genshi import Markup, Stream
from genshi.builder import tag
from pkg_resources import resource_filename

from trac.config import ListOption
from trac.core import Component, TracError, implements
from trac.db import DatabaseManager, Table, Column
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.resource import Resource, ResourceSystem, get_resource_description
from trac.resource import get_resource_url
from trac.util import get_reporter_id
from trac.util.compat import partial
from trac.util.datefmt import format_datetime, to_datetime, utc
from trac.util.text import to_unicode
from trac.web.api import IRequestFilter, IRequestHandler, Href
from trac.web.chrome import Chrome, ITemplateProvider, add_ctxtnav
from trac.web.chrome import add_notice, add_script, add_stylesheet
from trac.wiki.api import IWikiChangeListener, IWikiMacroProvider, parse_args


# Provide `resource_exists`, that has been backported to Trac 0.11.8 only.
try:
    from trac.resource import resource_exists
    resource_check = True
except ImportError:
    def resource_exists(env, resource):
        """Checks for resource existence without actually instantiating a
        model.

        :return: `True`, if the resource exists, `False` if it doesn't
        and `None` in case no conclusion could be made (i.e. when
        `IResourceManager.resource_exists` is not implemented).
        """
        manager = ResourceSystem(env).get_resource_manager(resource.realm)
        if manager and hasattr(manager, 'resource_exists'):
            return manager.resource_exists(resource)
        elif resource.id is None:
            return False
    resource_check = False

# Provide functions, that have been introduced in Trac 0.12.

try:
    from trac.util import as_int
except ImportError:
    def as_int(s, default, min=None, max=None):
        """Convert s to an int and limit it to the given range, or
        return default if unsuccessful (copied verbatim from Trac 1.0).
        """
        try:
            value = int(s)
        except (TypeError, ValueError):
            return default
        if min is not None and value < min:
            value = min
        if max is not None and value > max:
            value = max
        return value

try:
    from trac.util.datefmt import to_utimestamp
except ImportError:
    from trac.util.datefmt import to_timestamp
    def to_utimestamp(dt):
        return to_timestamp(dt) * 1000000

# That interface has been introduced in Trac 0.12 too.
has_milestonechangelistener = False
try:
    from trac.ticket.api import IMilestoneChangeListener
    has_milestonechangelistener = True
except ImportError:
    has_milestonechangelistener = False


def get_versioned_resource(env, resource):
    """Find the current version for a Trac resource.

    Because versioned resources with no version value default to 'latest',
    the current version has to be retrieved separately.
    """
    realm = resource.realm
    if realm == 'ticket':
        db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT SUM(c.change) FROM (
                SELECT 1 as change
                  FROM ticket_change
                 WHERE ticket=%s
                 GROUP BY time) AS c
            """, (resource.id,))
        tkt_changes = cursor.fetchone()
        resource.version = tkt_changes and tkt_changes[0] or 0
    elif realm == 'wiki':
        db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT version
              FROM wiki
             WHERE name=%s
             ORDER BY version DESC LIMIT 1
            """, (resource.id,))
        page_version = cursor.fetchone()
        resource.version = page_version and int(page_version[0]) or 0
    return resource

def resource_from_path(env, path):
    """Find realm and resource ID from resource URL.

    Assuming simple resource paths to convert to Trac resource identifiers.
    """
    if isinstance(path, basestring):
        path = path.strip('/')
        # Special-case: Default TracWiki start page.
        if path == 'wiki':
            path += '/WikiStart'
    for realm in ResourceSystem(env).get_known_realms():
        if path.startswith(realm):
            resource_id = re.sub(realm, '', path, 1).lstrip('/')
            resource = Resource(realm, resource_id)
            if not resource_check:
                return resource
            elif resource_exists(env, resource) in (None, True):
                return get_versioned_resource(env, resource)


class VoteSystem(Component):
    """Allow up- and down-voting on Trac resources."""

    implements(IEnvironmentSetupParticipant,
               IPermissionRequestor,
               IRequestFilter,
               IRequestHandler,
               ITemplateProvider,
               IWikiChangeListener,
               IWikiMacroProvider)
    if has_milestonechangelistener:
        implements(IMilestoneChangeListener)

    image_map = {-1: ('aupgray.png', 'adownmod.png'),
                  0: ('aupgray.png', 'adowngray.png'),
                 +1: ('aupmod.png', 'adowngray.png')}

    path_match = re.compile(r'/vote/(up|down)/(.*)')

    schema = [
        Table('votes', key=('realm', 'resource_id', 'username', 'vote'))[
            Column('realm'),
            Column('resource_id'),
            Column('version', 'int'),
            Column('username'),
            Column('vote', 'int'),
            Column('time', type='int64'),
            Column('changetime', type='int64'),
            ]
        ]
    # Database schema version identifier, used for automatic upgrades.
    schema_version = 2

    # Default database values
    #(table, (column1, column2), ((row1col1, row1col2), (row2col1, row2col2)))
    db_data = (
        ('permission',
            ('username', 'action'),
                (('anonymous', 'VOTE_VIEW'),
                 ('authenticated', 'VOTE_MODIFY'))),
        ('system',
            ('name', 'value'),
                (('vote_version', str(schema_version)),)))

    voteable_paths = ListOption('vote', 'paths', '/ticket*,/wiki*',
        doc='List of URL paths to allow voting on. Globs are supported.')

    ### Public methods

    def get_top_voted(self, req, realm=None, top=0):
        """Return resources ordered top-down by vote count."""
        args = []
        if realm:
            args.append(realm)
        if top:
            args.append(top)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT realm,resource_id,SUM(vote) AS count
              FROM votes%s
             GROUP by realm,resource_id
             ORDER by count DESC,resource_id%s
        """ % (realm and ' WHERE realm=%s' or '', top and ' LIMIT %s' or ''),
            args)
        rows = cursor.fetchall()
        for row in rows:
            yield row

    def get_vote_counts(self, resource):
        """Get negative, total and positive vote counts and return them in a
        tuple.
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT sum(vote)
              FROM votes
             WHERE realm=%s
               AND resource_id=%s
        """, (resource.realm, resource.id))
        total = cursor.fetchone()[0] or 0
        cursor.execute("""
            SELECT sum(vote)
              FROM votes
             WHERE vote < 0
               AND realm=%s
               AND resource_id=%s
        """, (resource.realm, resource.id))
        negative = cursor.fetchone()[0] or 0
        cursor.execute("""
            SELECT sum(vote)
              FROM votes
             WHERE vote > 0
               AND realm=%s
               AND resource_id=%s
        """, (resource.realm, to_unicode(resource.id)))
        positive = cursor.fetchone()[0] or 0
        return (negative, total, positive)

    def get_vote(self, req, resource):
        """Return the current users vote for a resource."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT vote
              FROM votes
             WHERE username=%s
               AND realm=%s
               AND resource_id=%s
        """, (get_reporter_id(req), resource.realm, to_unicode(resource.id)))
        row = cursor.fetchone()
        return row and row[0]

    def set_vote(self, req, resource, vote):
        """Vote for a resource."""
        now_ts = to_utimestamp(datetime.now(utc))
        args = list((now_ts, resource.version, vote, get_reporter_id(req),
                     resource.realm, to_unicode(resource.id)))
        if not resource.version:
            args.pop(1)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE votes
               SET changetime=%%s%s,vote=%%s
             WHERE username=%%s
               AND realm=%%s
               AND resource_id=%%s
        """ % (resource.version and ',version=%s' or ''), args)
        if self.get_vote(req, resource) is None:
            cursor.execute("""
                INSERT INTO votes
                    (realm,resource_id,version,username,vote,time,changetime)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (resource.realm, to_unicode(resource.id), resource.version,
                  get_reporter_id(req), vote, now_ts, now_ts))
        db.commit()

    def reparent_votes(self, resource, old_id):
        """Update resource reference of votes on a renamed resource."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE votes
               SET resource_id=%s
             WHERE realm=%s
               AND resource_id=%s
        """, (to_unicode(resource.id), resource.realm, to_unicode(old_id)))
        db.commit()

    def delete_votes(self, resource):
        """Delete votes for a resource."""
        args = list((resource.realm, to_unicode(resource.id)))
        if resource.version:
            args.append(resource.version)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            DELETE
              FROM votes
             WHERE realm=%%s
               AND resource_id=%%s%s
        """ % (resource.version and ' AND version=%s' or ''), args)
        db.commit()

    def get_votes(self, req, resource=None, top=0):
        """Return most recent votes, optionally only for one resource."""
        args = resource and [resource.realm, to_unicode(resource.id)] or []
        if top:
            args.append(top)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT realm,resource_id,vote,username,changetime
              FROM votes
             WHERE changetime is not NULL%s
             ORDER BY changetime DESC%s
        """ % (resource and ' AND realm=%s AND resource_id=%s' or '',
               top and ' LIMIT %s' or ''), args)
        rows = cursor.fetchall()
        for row in rows:
            yield row

    def get_total_vote_count(self, realm):
        """Return the total vote count for a realm, like 'ticket'."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT sum(vote) FROM votes WHERE resource LIKE %s',
                       (realm + '%',))
        total = cursor.fetchone()[0] or 0
        cursor.execute("""
            SELECT sum(vote)
              FROM votes
             WHERE vote < 0
               AND resource LIKE %s
        """, (realm + '%',))
        negative = cursor.fetchone()[0] or 0
        cursor.execute("""
            SELECT sum(vote)
              FROM votes
             WHERE vote > 0
               AND resource=%s
        """, (realm + '%',))
        positive = cursor.fetchone()[0] or 0
        return (negative, total, positive)

    def get_realm_votes(self, realm):
        """Return a dictionary of vote count for a realm."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT resource FROM votes WHERE resource LIKE %s',
                       (realm + '%',))
        resources = set([i[0] for i in cursor.fetchall()])
        votes = {}
        for resource in resources:
            votes[resource] = self.get_vote_counts(resource)
        return votes

    def get_max_votes(self, realm):
        votes = self.get_realm_votes(realm)
        if not votes:
            return 0
        return max([i[1] for i in votes.values()])

    ### IMilestoneChangeListener methods

    def milestone_created(self, milestone):
        """Called when a milestone is created."""
        pass

    def milestone_changed(self, milestone, old_values):
        """Called when a milestone is modified."""
        old_name = old_values.get('name')
        if old_name and milestone.resource.id != old_name:
            self.reparent_votes(milestone.resource, old_name)

    def milestone_deleted(self, milestone):
        """Called when a milestone is deleted."""
        self.delete_votes(milestone.resource)

    ### IPermissionRequestor method
    def get_permission_actions(self):
        action = 'VOTE_VIEW'
        return [('VOTE_MODIFY', [action]), action]

    ### IRequestHandler methods

    def match_request(self, req):
        return 'VOTE_VIEW' in req.perm and self.path_match.match(req.path_info)

    def process_request(self, req):
        req.perm.require('VOTE_MODIFY')
        match = self.path_match.match(req.path_info)
        vote, path = match.groups()
        resource = resource_from_path(self.env, path)
        vote = vote == 'up' and +1 or -1
        old_vote = self.get_vote(req, resource)

        # Protect against CSRF attacks: Validate the token like done in Trac
        # core for all POST requests with a content-type corresponding
        # to form submissions.
        msg = ''
        if req.args.get('token') != req.form_token:
            if self.env.secure_cookies and req.scheme == 'http':
                msg = ("Secure cookies are enabled, you must use https for "
                       "your requests.")
            else:
                msg = ("Do you have cookies enabled?")
            raise TracError(msg)
        else:
            if old_vote == vote:
                # Second click on same icon revokes previous vote.
                vote = 0
            self.set_vote(req, resource, vote)

        if req.args.get('js'):
            body, title = self.format_votes(resource)
            content = ':'.join(
                          (req.href.chrome('vote/' + self.image_map[vote][0]),
                           req.href.chrome('vote/' + self.image_map[vote][1]),
                           body, title))
            if isinstance(content, unicode):
                content = content.encode('utf-8')
            req.send(content)

        req.redirect(get_resource_url(self.env, resource(version=None),
                                      req.href))

    ### IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if 'VOTE_VIEW' in req.perm:
            for path in self.voteable_paths:
                if fnmatchcase(req.path_info, path) and \
                        resource_from_path(self.env, req.path_info):
                    self.render_voter(req)
                    break
        return template, data, content_type

    ### ITemplateProvider methods

    def get_templates_dirs(self):
        return []
        #resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('vote', resource_filename(__name__, 'htdocs'))]

    ### IWikiChangeListener methods

    def wiki_page_added(self, page):
        """Called whenever a new Wiki page is added."""
        pass

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        """Called when a page has been modified."""
        pass

    def wiki_page_deleted(self, page):
        """Called when a page has been deleted."""
        page.resource.version = None
        self.delete_votes(page.resource)

    def wiki_page_version_deleted(self, page):
        """Called when a version of a page has been deleted."""
        self.delete_votes(page.resource)

    def wiki_page_renamed(self, page, old_name): 
        """Called when a page has been renamed."""
        # Correct references for all page versions.
        page.resource.version = None
        # Work around issue t:#11138.
        page.resource.id = page.name
        self.reparent_votes(page.resource, old_name)

    ### IWikiMacroProvider methods
    def get_macros(self):
        yield 'LastVoted'
        yield 'TopVoted'
        yield 'VoteList'

    def get_macro_description(self, name):
        if name == 'LastVoted':
            return "Show most recently voted resources."
        elif name == 'TopVoted':
            return "Show listing of voted resources ordered by total score."
        elif name == 'VoteList':
            return "Show listing of most recent votes for a resource."

    def expand_macro(self, formatter, name, content):
        env = formatter.env
        req = formatter.req
        if not 'VOTE_VIEW' in req.perm:
            return
        # Simplify function calls.
        format_author = partial(Chrome(self.env).format_author, req)
        if not content:
            args = []
            compact = None
            kw = {}
            top = 5
        else:
            args, kw = parse_args(content)
            compact = 'compact' in args and True
            top = as_int(kw.get('top'), 5, min=0)

        if name == 'LastVoted':
            lst = tag.ul()
            for i in self.get_votes(req, top=top):
                resource = Resource(i[0], i[1])
                # Anotate who and when.
                voted = ('by %s at %s'
                         % (format_author(i[3]),
                            format_datetime(to_datetime(i[4]))))
                lst(tag.li(tag.a(
                    get_resource_description(env, resource, compact and
                                             'compact' or 'default'),
                    href=get_resource_url(env, resource, formatter.href),
                    title=(compact and '%+i %s' % (i[2], voted) or None)),
                    (not compact and Markup(' %s %s' % (tag.b('%+i' % i[2]),
                                                        voted)) or '')))
            return lst

        elif name == 'TopVoted':
            realm = kw.get('realm')
            lst = tag.ul()
            for i in self.get_top_voted(req, realm=realm, top=top):
                if 'up-only' in args and i[2] < 1:
                    break
                resource = Resource(i[0], i[1])
                lst(tag.li(tag.a(
                    get_resource_description(env, resource, compact and
                                             'compact' or 'default'),
                    href=get_resource_url(env, resource, formatter.href),
                    title=(compact and '%+i' % i[2] or None)),
                    (not compact and ' (%+i)' % i[2] or '')))
            return lst

        elif name == 'VoteList':
            lst = tag.ul()
            resource = resource_from_path(env, req.path_info)
            for i in self.get_votes(req, resource, top=top):
                vote = ('at %s' % format_datetime(to_datetime(i[4])))
                lst(tag.li(
                    compact and format_author(i[3]) or
                    Markup(u'%s by %s %s' % (tag.b('%+i' % i[2]),
                                             tag(format_author(i[3])), vote)),
                    title=(compact and '%+i %s' % (i[2], vote) or None)))
            return lst

    ### IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        if self.get_schema_version(db) < self.schema_version:
            return True
        elif self.get_schema_version(db) > self.schema_version:
            raise TracError(
                "A newer version of VotePlugin has been installed before, "
                "but downgrading is unsupported.")
        return False

    def upgrade_environment(self, db):
        """Each schema version should have its own upgrade module, named
        upgrades/dbN.py, where 'N' is the version number (int).
        """
        db_mgr = DatabaseManager(self.env)
        schema_ver = self.get_schema_version(db)

        cursor = db.cursor()
        # Is this a new installation?
        if not schema_ver:
            # Perform a single-step install: Create plugin schema and
            # insert default data into the database.
            connector = db_mgr._get_connector()[0]
            for table in self.schema:
                for stmt in connector.to_sql(table):
                    self.env.log.debug(stmt)
                    cursor.execute(stmt)
            for table, cols, vals in self.db_data:
                cursor.executemany("INSERT INTO %s (%s) VALUES (%s)"
                                   % (table, ','.join(cols),
                                      ','.join(['%s' for c in cols])), vals)
        elif schema_ver < self.schema_version:
            # Perform incremental upgrades.
            for i in range(schema_ver + 1, self.schema_version + 1):
                name  = 'db%i' % i
                try:
                    upgrades = __import__('tracvote.upgrades', globals(),
                                          locals(), [name])
                    script = getattr(upgrades, name)
                except AttributeError:
                    raise TracError("No upgrade module for version "
                                    "%(num)i (%(version)s.py)",
                                    num=i, version=name)
                script.do_upgrade(self.env, i, cursor)
        else:
            # Obsolete call handled gracefully.
            return
        cursor.execute("""
            UPDATE system
               SET value=%s
             WHERE name='vote_version'
            """, (self.schema_version,))
        self.log.info("Upgraded VotePlugin db schema from version %d to %d"
                      % (schema_ver, self.schema_version))
        db.commit()

    ### Internal methods

    def get_schema_version(self, db=None):
        """Return the current schema version for this plugin."""
        db = db and db or self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='vote_version'
        """)
        row = cursor.fetchone()
        schema_ver = row and int(row[0]) or 0
        if schema_ver > 1:
            # The expected outcome for any recent installation.
            return schema_ver
        # Care for pre-tracvote-0.2 installations.
        dburi = self.config.get('trac', 'database')
        tables = self._get_tables(dburi, cursor)
        if 'votes' in tables:
            return 1
        # This is a new installation.
        return 0

    def render_voter(self, req):
        path = req.path_info.strip('/')
        resource = resource_from_path(self.env, path)
        vote = resource and self.get_vote(req, resource) or 0
        up = tag.img(src=req.href.chrome('vote/' + self.image_map[vote][0]),
                     alt='Up-vote')
        down = tag.img(src=req.href.chrome('vote/' + self.image_map[vote][1]),
                       alt='Down-vote')
        if not 'action' in req.args and 'VOTE_MODIFY' in req.perm and \
                get_reporter_id(req) != 'anonymous':
            down = tag.a(down, id='downvote',
                         href=req.href.vote('down', path,
                                            token=req.form_token),
                         title='Down-vote')
            up = tag.a(up, id='upvote',
                       href=req.href.vote('up', path, token=req.form_token),
                       title='Up-vote')
            add_script(req, 'vote/js/tracvote.js')
            shown = req.session.get('shown_vote_message')
            if not shown:
                add_notice(req, 'You can vote for resources on this Trac '
                           'install by clicking the up-vote/down-vote arrows '
                           'in the context navigation bar.')
                req.session['shown_vote_message'] = '1'
        body, title = self.format_votes(resource)
        votes = tag.span(body, id='votes')
        add_stylesheet(req, 'vote/css/tracvote.css')
        elm = tag.span(up, votes, down, id='vote', title=title)
        req.chrome.setdefault('ctxtnav', []).insert(0, elm)

    def format_votes(self, resource):
        """Return a tuple of (body_text, title_text) describing the votes on a
        resource.
        """
        negative, total, positive = resource and \
                                    self.get_vote_counts(resource) or (0,0,0)
        count_detail = ['%+i' % i for i in (positive, negative) if i]
        if count_detail:
            count_detail = ' (%s)' % ', '.join(count_detail)
        else:
            count_detail = ''
        return ('%+i' % total, 'Vote count%s' % count_detail)

    def _get_tables(self, dburi, cursor):
        """Code from TracMigratePlugin by Jun Omae (see tracmigrate.admin)."""
        if dburi.startswith('sqlite:'):
            sql = """
                SELECT name
                  FROM sqlite_master
                 WHERE type='table'
                   AND NOT name='sqlite_sequence'
            """
        elif dburi.startswith('postgres:'):
            sql = """
                SELECT tablename
                  FROM pg_tables
                 WHERE schemaname = ANY (current_schemas(false))
            """
        elif dburi.startswith('mysql:'):
            sql = "SHOW TABLES"
        else:
            raise TracError('Unsupported database type "%s"'
                            % dburi.split(':')[0])
        cursor.execute(sql)
        return sorted([row[0] for row in cursor])
