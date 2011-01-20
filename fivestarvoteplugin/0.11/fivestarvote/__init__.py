# Based on code from : http://trac-hacks.org/wiki/VotePlugin
# Ported to a 5 star style voting system

import re
from trac.core import *
from trac.config import ListOption
from trac.env import IEnvironmentSetupParticipant
from trac.web.api import IRequestFilter, IRequestHandler, Href
from trac.web.chrome import ITemplateProvider, add_ctxtnav, add_stylesheet, \
                            add_script, add_notice
from trac.resource import get_resource_url
from trac.db import DatabaseManager, Table, Column
from trac.perm import IPermissionRequestor
from trac.util import get_reporter_id
from genshi import Markup, Stream
from genshi.builder import tag
from pkg_resources import resource_filename


class FiveStarVoteSystem(Component):
    """Allow up and down-voting on Trac resources."""

    implements(ITemplateProvider, IRequestFilter, IRequestHandler,
               IEnvironmentSetupParticipant, IPermissionRequestor)

    voteable_paths = ListOption('fivestarvote', 'paths', '^/$,^/wiki*,^/ticket*',
        doc='List of URL paths to allow voting on. Globs are supported.')

    schema = [
        Table('fivestarvote', key=('resource', 'username', 'vote'))[
            Column('resource'),
            Column('username'),
            Column('vote', 'int'),
            ]
        ]

    path_match = re.compile(r'/fivestarvote/([1-5])/(.*)')


    # Public methods
    def get_vote_counts(self, resource):
        """Get total, count and tally vote counts and return them in a tuple."""
        resource = self.normalise_resource(resource)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = "select sum(vote), count(*) from fivestarvote where (resource = '%s')" % resource
        self.env.log.debug("sql:: %s" % sql)
        cursor.execute(sql)
        row = cursor.fetchone()
        sum = row[0] or 0
        total = row[1] or 0
        tally = 0
        if (total > 0):
            tally = (sum / total)
        return (sum, total, tally)

    def get_vote(self, req, resource):
        """Return the current users vote for a resource."""
        resource = self.normalise_resource(resource)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT vote FROM fivestarvote WHERE username=%s '
                       'AND resource = %s', (get_reporter_id(req), resource))
        row = cursor.fetchone()
        vote = row and row[0] or 0
        return vote

    def set_vote(self, req, resource, vote):
        """Vote for a resource."""
        resource = self.normalise_resource(resource)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('DELETE FROM fivestarvote WHERE username=%s '
                       'AND resource = %s', (get_reporter_id(req), resource))
        if vote:
            cursor.execute('INSERT INTO fivestarvote (resource, username, vote) '
                           'VALUES (%s, %s, %s)',
                           (resource, get_reporter_id(req), vote))
        db.commit()

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['VOTE_VIEW', 'VOTE_MODIFY']

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        return [('fivestarvote', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods
    def match_request(self, req):
        return 'VOTE_VIEW' in req.perm and self.path_match.match(req.path_info)

    def process_request(self, req):
        req.perm.require('VOTE_MODIFY')
        match = self.path_match.match(req.path_info)
        vote, resource = match.groups()
        resource = self.normalise_resource(resource)

        self.set_vote(req, resource, vote)
        self.env.log.debug("DAV::")

        if req.args.get('js'):
            percent, str, title = self.format_votes(resource)
            req.send(','.join(("%s" % percent, str, title)))
        
        req.redirect(req.get_header('Referer'))

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if 'VOTE_VIEW' not in req.perm:
            return handler

        for path in self.voteable_paths:
            if re.match(path, req.path_info):
                self.render_voter(req)
                break

        return handler

    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("select count(*) from fivestarvote")
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

    # Internal methods
    def render_voter(self, req):
        resource = self.normalise_resource(req.path_info)

        count = self.get_vote_counts(resource)

        add_stylesheet(req, 'fivestarvote/css/fivestarvote.css')

        names = ['', 'one', 'two', 'three', 'four', 'five']
        els = []
        percent = 0
        if count[2] > 0:
            percent = count[2] * 20

        str = "Currently %s/5 stars." % count[2]
        sign = '%'
        style = "width: %s%s" % (percent, sign)
        li = tag.li(str, class_='current-rating', style=style)
        els.append(li)
        for i in range(1, 6):
            className = "item %s-star" % names[i]
            href = "#"
            if 'VOTE_MODIFY' in req.perm and get_reporter_id(req) != 'anonymous':
                href = req.href.fivestarvote(i, resource)
                add_script(req, 'fivestarvote/js/fivestarvote.js', mimetype='text/javascript')
            a = tag.a(i, href=href, class_=className)
            li = tag.li(a)
            els.append(li)
        
        ul = tag.ul(els, class_='star-rating')
        className = ''
        if 'VOTE_MODIFY' in req.perm and get_reporter_id(req) != 'anonymous':
            className = 'active'
        title = "Current Vote: %s users voted for a total of %s" % (count[1], count[0]) 
        add_ctxtnav(req, tag.span(tag.object(ul), id='fivestarvotes', title=title, class_=className))


    def normalise_resource(self, resource):
        if isinstance(resource, basestring):
            resource = resource.strip('/')
            # Special-case start page
            if not resource or resource == 'wiki':
                resource += '/WikiStart'
            return resource
        return get_resource_url(self.env, resource, Href('')).strip('/')

    def format_votes(self, resource):
        count = self.get_vote_counts(resource)

        percent = 0
        if count[2] > 0:
            percent = count[2] * 20

        str = "Currently %s/5 stars." % count[2]
        title = "Current Vote: %s users voted for a total of %s" % (count[1], count[0]) 
        return (percent, str, title)
