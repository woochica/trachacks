import time
import re
from datetime import date, timedelta
from pkg_resources import resource_filename

from genshi.builder import tag

from trac.config import Option, ListOption
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

    # Default work week.
    work_days = ListOption('team-calendar',
                            'work_days',
                            [],
                            doc="Lists days of week that are worked. " + \
                                "Defaults to none.  0 is Monday.")

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
                                 'WHERE ondate >= %%s AND ondate <= %%s '
                                 'GROUP BY ondate, username, availability' % \
                                     self.table_name, 
                                      (from_date.isoformat(), 
                                      to_date.isoformat(),))
        
        empty_day = dict([(p, 0.0) for p in people])
        full_day = dict([(p, 1.0) for p in people])

        timetable = {}
        current_date = from_date
        while current_date <= to_date:
            # work_days contains strings because ListOption returns a
            # list of strings.  Even if it had numbers, we couldn't
            # include Monday (0) because of
            # http://trac.edgewall.org/ticket/10541
            if str(current_date.weekday()) in self.work_days:
                timetable[current_date] = full_day.copy()
            else:
                timetable[current_date] = empty_day.copy()
            current_date += timedelta(1)
            
        for row in timetable_cursor:
            timetable[row[0]][row[1]] = row[2]
            
        return timetable
        
    # tuples is a list of arrays.
    # each array is (datetime, user, true/false).  For example:
    #  [(datetime.date(2011, 11, 28), u'admin', False), 
    #   (datetime.date(2011, 11, 28), u'chrisn', True),
    #   (datetime.date(2011, 11, 29), u'admin', False),
    #   (datetime.date(2011, 11, 29), u'chrisn', True)]
    # Note that the date and user are keys to the DB.
    #
    # It appears -- though I don't know that it is guaranteed -- that
    # the items are in date order and there are no gaps in the dates.
    def update_timetable(self, tuples):
        db = self.env.get_db_cnx()

        # See what's already in the database for the same date range.
        fromDate = tuples[1][0]
        toDate = tuples[-1][0]
        users = []
        for (date, user, avail) in tuples:
            if user not in users:
                users.append(user)
        cursor = db.cursor()
        # In 0.12, we could do
        #
        #   ','.join([db.quote(user) for user in users])
        #
        # but 0.11 doesn't have db.quote() so we build up enough
        # instances of %s to accomodate all the users then let
        # cursor.execute() quote the items from the list.
        inClause = "username IN (%s)" % ','.join(('%s',) * len(users))
        cursor.execute("SELECT ondate, username, availability FROM %s " % \
                           self.table_name +
                       "WHERE ondate >= %s AND ondate <= %s " +
                       "AND " + inClause,
                       [fromDate.isoformat(), toDate.isoformat()] + users)

        updates = []
        inserts = []
        keys = [(t[0], t[1]) for t in tuples]
        for row in cursor:
            key = (row[0], row[1])
            # If the whole db row is in tuples (date, person, and
            # availability match) take it out of tuples, we don't need
            # to do anything to the db
            if row in tuples:
                tuples.remove(row)
                keys.remove(key)
            # If the db key in this row has a value in tuples, we need
            # to update availability
            elif key in keys:
                index = keys.index(key)
                updates.append(tuples.pop(index))
                keys.pop(index)
            # The query results should cover the same date range as
            # tuples.  We might get here if tuples has more users than
            # the db.  We fall through and add any tuples that don't
            # match the DB so this is OK
            else:
                self.env.log.info('UI and db inconsistent.')

        # Duplicates and updates have been removed from tuples so
        # what's left is things to insert.
        inserts = tuples

        if len(inserts):
            insert_cursor = db.cursor()
            valuesClause = ','.join(('(%s,%s,%s)',) * len(inserts))
            # FIXME - we likely want to do this earlier on all of tuples.
            inserts = [(t[0], t[1], t[2] and 1 or 0) for t in inserts]
            # Quickly flatten the list.  List comprehension is always
            # weird.  See http://stackoverflow.com/questions/952914
            flat = [item for sublist in inserts for item in sublist]
            insert_cursor.execute("INSERT INTO %s " % self.table_name + \
                                      "(ondate, username, availability) " + \
                                      "VALUES %s" % valuesClause,
                                  flat)

        if len(updates):
            update_cursor = db.cursor()
            for t in updates:
                update_cursor.execute("UPDATE %s " % self.table_name + \
                                          "SET availability = %d " % \
                                          (t[2] and 1 or 0) + \
                                          "WHERE ondate = %s "
                                          "AND username = %s;",
                                      (t[0], t[1]))

        if len(inserts) or len(updates):
            db.commit()
    
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
