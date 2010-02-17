# Narcissus plugin for Trac

import datetime
from settings import *
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider,\
    add_stylesheet, add_script
from trac.web.main import IRequestHandler
from trac.util import escape, Markup
from trac.ticket.model import Ticket
from trac.wiki.model import WikiPage

ticket_query = '''select time, id, reporter, "created" from ticket where %s union all 
    select time, ticket, author, "commented on" from ticket_change where field = "comment" 
    and %s group by time union all select time, ticket, author, "updated" from 
    ticket_change where field != "resolution" and field != "comment" and newvalue != 
    "closed" and newvalue != "reopened" and %s group by time union all select time, ticket, 
    author, "closed" from ticket_change where newvalue = "closed" and %s union all select 
    time, ticket, author, "reopened" from ticket_change where newvalue = "reopened" and %s 
    order by time'''
_DSQL = {'wiki': ('select time, name, author, version from wiki where time >= %s and time < %s',  1),
        'svn': ('select time, rev, author from revision where time >= %s and time < %s', 1), 
        'ticket': (ticket_query % (('time >= %s and time < %s',) * 5), 5),
        'tid': (ticket_query % (('id = %s',) + ('ticket = %s',) * 4), 5)
       }

class NarcissusPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'narcissus'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/details'

    def process_request(self, req):
        add_stylesheet(req, 'nar/css/narcissus.css')
        add_script(req, 'nar/js/narcissus.js')

        self.db = self.env.get_db_cnx()
        self._settings = NarcissusSettings(self.db)

        self._details(req)

        return 'details.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return a list of directories containing the provided ClearSilver
        templates.
        """

        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('nar', resource_filename(__name__, 'htdocs'))]

    def _details(self, req):
        # Get the activity details according to the request
        member = req.args.get('member', None)
        resource = req.args.get('resource', None)
        date = req.args.get('date', None)
        tid = req.args.get('tid', None)        
        cursor = self.db.cursor()

        # ticket view will request ticket details according to tid
        if tid:
            cursor.execute(_DSQL['tid'][0] % ((tid,) * _DSQL['tid'][1]))
            resource = 'ticket'
        else:
            next_date = float(date) + 24 * 60 * 60
            cursor.execute(_DSQL[resource][0] % ((date, next_date) * _DSQL[resource][1]))
            self._score(req)
        
        # not casting row to separate variables, as result will be different for each query
        for i, row in enumerate(cursor):
            # group view will request activity details for a group member
            if member and row[2] != member:
                continue
            elif row[2] in self._settings.members:
                eid = row[1]
                req.hdf['%s.%s_%s.author' % (resource, eid, i)] = row[2]
                req.hdf['%s.%s_%s.time' % (resource, eid, i)] = self._timestr(row[0])
                if resource == 'ticket' or tid:
                    req.hdf['ticket.%s_%s.tid' % (eid, i)] = eid
                    req.hdf['ticket.%s_%s.action' % (eid, i)] = row[3]
                    req.hdf['ticket.%s_%s.url' % (eid, i)] = '%s/ticket/%s'\
                        % (req.base_url, eid)
                elif resource == 'wiki':
                    req.hdf['wiki.%s_%s.name' % (eid, i)] = eid
                    url = eid.replace(' ', '%20')
                    url = url.replace("'", '%27')
                    req.hdf['wiki.%s_%s.url' % (eid, i)] = '%s/wiki/%s'\
                        % (req.base_url, url)
                    if row[3] > 1:
                        req.hdf['wiki.%s_%s.diff' % (eid, i)] = '?action=diff&version=%s' % row[3]
                elif resource == 'svn':
                    req.hdf['svn.%s_%s.rev' % (eid, i)] = eid
                    req.hdf['svn.%s_%s.url' % (eid, i)] = '%s/changeset/%s'\
                        % (req.base_url, eid)
                # ensure time includes date as well as time for ticket view
                if tid:
                    req.hdf['ticket.%s_%s.time' % (tid, i)] = self._datetimestr(row[0])

    def _score(self, req):
        # Get the scored activity according to the request (for group and project view)
        cursor = self.db.cursor()
        member = req.args.get('member', None)
        resource = req.args.get('resource', None)
        date = req.args.get('date', None)
        next_date = float(date) + 24 * 60 * 60

        metric = 'line%s added'
        if resource == 'ticket':
            metric = 'credit%s'

        if member:
            sql = '''select * from narcissus_data where member = "%s" 
                and resource = "%s" and dtime >= %s and dtime < %s'''\
                % (member, resource, date, next_date)
        else:
            sql = '''select * from narcissus_data where resource = "%s"
                and dtime >= %s and dtime < %s''' % (resource, date, next_date)

        cursor.execute(sql)
        
        i = 0
        for member, dtime, eid, resource, type, value in cursor:
            req.hdf['score.%s.eid' % i] = eid
            req.hdf['score.%s.type' % i] = type
            activity = '%s %s' % (value, metric % ('','s')[int(value) > 1])
            req.hdf['score.%s.activity' % i] = activity
            i += 1
        
        settings = NarcissusSettings(self.db)
        bounds = settings.bounds[resource]
        
        metric = 'added lines'
        if resource == 'ticket':
            metric = 'credits'

        req.hdf['bounds'] = resource
        for i, x in enumerate(bounds):
            value = '%d point%s for up to %d %s' % (i + 1, ('','s')[i != 0], x, metric)
            req.hdf['bounds.%s' % i] = value
        value = '%d points for over %d %s' % (i + 2, x, metric)
        req.hdf['bounds.%s' % (i + 1)] = value

    def _timestr(self, timestamp):
        # Given a timestamp, return the time string format hh:ss
        d = datetime.datetime.fromtimestamp(timestamp)
        return d.strftime('%H:%M')

    def _datetimestr(self, timestamp):
        # Given a timestamp, return the datetime string format 
        d = datetime.datetime.fromtimestamp(timestamp)
        return d.strftime('%d/%m/%y %H:%M')
