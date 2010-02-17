# Narcissus plugin for Trac

import datetime
from settings import *
from trac.core import *
from trac.web.chrome import INavigationContributor
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
    implements(INavigationContributor, IRequestHandler)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'narcissus'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/details'

    def process_request(self, req):
        self.db = self.env.get_db_cnx()
        self._settings = NarcissusSettings(self.db)

        params = {}
        params['ticket'] = []
        params['wiki'] = []
        params['svn'] = []
        self._details(req, params)

        return 'details.xhtml', params, None

    def _details(self, req, params):
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
            self._score(req, params)
        
        # not casting row to separate variables, as result will be different for each query
        for i, row in enumerate(cursor):
            # group view will request activity details for a group member
            if member and row[2] != member:
                continue
            elif row[2] in self._settings.members:
                item = {}
                eid = row[1]
                item['author'] = row[2]
                item['time'] = self._timestr(row[0])
                if resource == 'ticket' or tid:
                    item['tid'] = eid
                    item['action'] = row[3]
                    item['url'] = '%s/ticket/%s' % (req.base_url, eid)
                elif resource == 'wiki':
                    item['name'] = eid
                    url = eid.replace(' ', '%20')
                    url = url.replace("'", '%27')
                    item['url'] = '%s/wiki/%s' % (req.base_url, url)
                    item['diff'] = None
                    if row[3] > 1:
                        item['diff'] = '?action=diff&version=%s' % row[3]
                elif resource == 'svn':
                    item['rev'] = eid
                    item['url'] = '%s/changeset/%s' % (req.base_url, eid)
                # ensure time includes date as well as time for ticket view
                if tid:
                    item['time'] = self._datetimestr(row[0])
                params[resource].append(item)

    def _score(self, req, params):
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
        
        scores = []
        for member, dtime, eid, resource, type, value in cursor:
            score = {}
            score['eid'] = eid
            score['type'] = type
            activity = '%s %s' % (value, metric % ('','s')[int(value) > 1])
            score['activity'] = activity
            scores.append(score)
        params['scores'] = scores
        
        settings = NarcissusSettings(self.db)
        bounds = settings.bounds[resource]
        
        metric = 'added lines'
        if resource == 'ticket':
            metric = 'credits'

        params['resource'] = resource
        boundsout = []
        for i, x in enumerate(bounds):
            value = '%d point%s for up to %d %s' % (i + 1, ('','s')[i != 0], x, metric)
            boundsout.append(value)
        value = '%d points for over %d %s' % (i + 2, x, metric)
        boundsout.append(value)
        params['bounds'] = boundsout

    def _timestr(self, timestamp):
        # Given a timestamp, return the time string format hh:ss
        d = datetime.datetime.fromtimestamp(timestamp)
        return d.strftime('%H:%M')

    def _datetimestr(self, timestamp):
        # Given a timestamp, return the datetime string format 
        d = datetime.datetime.fromtimestamp(timestamp)
        return d.strftime('%d/%m/%y %H:%M')
