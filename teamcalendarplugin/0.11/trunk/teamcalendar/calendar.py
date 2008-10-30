import time
import re
from datetime import date, timedelta
from pkg_resources import resource_filename

from genshi.builder import tag

from trac.config import Option
from trac.perm import PermissionSystem, IPermissionRequestor
from trac.core import Component, implements
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet

class TeamCalendar(Component):
    implements(INavigationContributor, IRequestHandler, IPermissionRequestor, ITemplateProvider)

    # Table name
    table_name = Option('team-calendar', 'table_name', u"team_availability", doc="The table that contains team availability information")

    # How much to display by default?
    weeks_prior = Option('team-calendar', 'weeks_prior', u"1", doc="Defines how many weeks before the current week to show by default")
    weeks_after = Option('team-calendar', 'weeks_after', u"3", doc="Defines how many weeks before the current week to show by default")

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'teamcalendar'

    def get_navigation_items(self, req):
        if 'TEAMCALENDAR_VIEW' in req.perm:
            yield ('mainnav', 'teamcalendar',
                   tag.a('Team Calendar', href=req.href.teamcalendar()))

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['TEAMCALENDAR_VIEW', 'TEAMCALENDAR_UPDATE_OTHERS', 'TEAMCALENDAR_UPDATE_OWN']

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('teamcalendar', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods
    def match_request(self, req):
        return re.match(r'/teamcalendar(?:_trac)?(?:/.*)?$', req.path_info)

    def get_people(self):
        perm = PermissionSystem(self.env)
        people = set(perm.get_users_with_permission('TEAMCALENDAR_UPDATE_OWN'))
        return sorted(people)

    def get_timetable(self, from_date, to_date, people):
        db = self.env.get_db_cnx()
        timetable_cursor = db.cursor()
        timetable_cursor.execute('SELECT ondate, username, availability '
                                 'FROM %s '
                                 'WHERE ondate >= "%s" AND ondate <= "%s" '
                                 'GROUP BY ondate, username' % (self.table_name, from_date.isoformat(), to_date.isoformat(),))
        
        empty_day = dict([(p, 0.0) for p in people])
        
        timetable = {}
        current_date = from_date
        while current_date <= to_date:
            timetable[current_date] = empty_day.copy()
            current_date += timedelta(1)
            
        for row in timetable_cursor:
            timetable[row[0]][row[1]] = row[2]
            
        return timetable
        
    def update_timetable(self, tuples):
        db = self.env.get_db_cnx()
        insert_cursor = db.cursor()
        # XXX: This is MySQL specific
        insert_cursor.execute("INSERT INTO %s (ondate, username, availability) VALUES %s "
                              "ON DUPLICATE KEY UPDATE availability = VALUES(availability)" %
                                (self.table_name,
                                 ", ".join(["('%s', '%s', %d)" % (t[0], t[1], t[2] and 1 or 0,) for t in tuples])))
    
    def string_to_date(self, date_str, fallback=None):
        try:
            date_tuple = time.strptime(date_str, '%Y-%m-%d')
            return date(date_tuple[0], date_tuple[1], date_tuple[2])
        except ValueError:
            return fallback
    
    def find_default_start(self):
        today = date.today()
        offset = (today.isoweekday() - 1) + (7 * int(self.weeks_prior))
        return today - timedelta(offset)
        
    def find_default_end(self):
        today = date.today()
        offset = (7 - today.isoweekday()) + (7 * int(self.weeks_after))
        return today + timedelta(offset)
    
    def process_request(self, req):
        req.perm.require('TEAMCALENDAR_VIEW')
        
        data = {}
                
        from_date = self.string_to_date(req.args.get('from_date', ''), self.find_default_start())
        to_date = self.string_to_date(req.args.get('to_date', ''), self.find_default_end())

        # Message
        data['message'] = ""

        # Current user
        data['authname'] = authname = req.authname

        # Can we update?

        data['can_update_own'] = can_update_own = ('TEAMCALENDAR_UPDATE_OWN' in req.perm)
        data['can_update_others'] = can_update_others = ('TEAMCALENDAR_UPDATE_OTHERS' in req.perm)
        data['can_update'] = (can_update_own or can_update_others)

        # Store dates
        data['today'] = date.today()
        data['from_date'] = from_date
        data['to_date'] = to_date
        
        # Get all people
        data['people'] = people = self.get_people()
        
        # Update timetable if required
        if 'update_calendar' in req.args:
            req.perm.require('TEAMCALENDAR_UPDATE_OWN')
            
            # deliberately override dates: want to show result of update
            from_date = current_date = self.string_to_date(req.args['orig_from_date'])
            to_date = self.string_to_date(req.args['orig_to_date'])
            tuples = []
            while current_date <= to_date:
                if can_update_others:
                    for person in people:
                        status = bool(req.args.get(u'%s.%s' % (current_date.isoformat(), person,), False))
                        tuples.append((current_date, person, status,))
                elif can_update_own:
                    status = bool(req.args.get(u'%s.%s' % (current_date.isoformat(), authname,), False))
                    tuples.append((current_date, authname, status,))
                current_date += timedelta(1)

            self.update_timetable(tuples)
            data['message'] = "Updated database."
        
        # Get the current timetable
        timetable = self.get_timetable(from_date, to_date, people)
        
        data['timetable'] = []
        current_date = from_date
        while current_date <= to_date:
            data['timetable'].append(dict(date=current_date, people=timetable[current_date]))
            current_date += timedelta(1)
        
        add_stylesheet(req, 'teamcalendar/css/calendar.css')
        return 'teamcalendar.html', data, None