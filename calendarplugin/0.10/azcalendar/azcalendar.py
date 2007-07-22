# -*-coding:utf-8-*-

import textwrap
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from schema import schema, schema_version, Event, EventPriority, EventType
from compat import schema_to_sql
import time
import calendar
import caltools
import cal_layout

class UserbaseModule(Component):
    implements(INavigationContributor,
               IRequestHandler,
               ITemplateProvider,
               IEnvironmentSetupParticipant,
               IPermissionRequestor)


    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'azcalendar'

    def get_navigation_items(self, req):
        yield 'mainnav', 'azcalendar', Markup('<a href="%s">Azcalendar</a>',
                self.env.href.azcalendar())


    # IRequestHandler methods

    def match_request(self, req):
        return "azcalendar" in req.path_info

    def process_add(self, req):
        add_stylesheet (req, 'hw/css/azcalendar.css')

        if req.method == 'GET' and req.args.has_key('date'):
            req.hdf['azcalendar.time_begin'] = time.strftime("%Y/%m/%d",(time.strptime(req.args['date'],"%Y%m%d")))
            req.hdf['azcalendar.time_end'] = time.strftime("%Y/%m/%d",(time.strptime(req.args['date'],"%Y%m%d")))
            return 'add_event.cs', None

        elif req.method == 'GET' and req.args.has_key('new_event'):
            begin_time, end_time, begin_stamp, end_stamp \
              = caltools.parse_time_begin_end(req.args['time_begin'], req.args['time_end'])

            date = time.strftime("%Y%m%d", begin_time)
            req.hdf['redir_url'] = str(self.env.href.azcalendar()) + "?date=%s" % date

            current_stamp = int(time.time())

            # Events with id 0 are created automatically by a DB layer.
            author = req.authname
            evt = Event(0, author, current_stamp, current_stamp, begin_stamp, end_stamp,
                        req.args['type'], req.args['priority'], req.args['title'])

            return evt.save(self.env, req)

    def process_show(self, req):
        def get_week(date):
            # If there is a simpler way to do this, let me know.  For now...
            d_year, d_doy, d_dow = date[0], date[-2], date[-3]

            doy_start = d_doy - d_dow
            y_start = d_year
            if doy_start < 1:
                y_start -= 1
                doy_start += 365 + int (calendar.isleap (y_start))

            doy_end = d_doy - d_dow + 7
            y_end = d_year
            if doy_end > 365 + int (calendar.isleap (y_end)):
                doy_end -= 365 + int (calendar.isleap (y_end))
                y_end += 1

            week_start = time.strptime (str(y_start) + str(doy_start), "%Y%j")
            week_end = time.strptime (str(y_end) + str(doy_end), "%Y%j")
            return week_start, week_end

        def get_month(date):
            d_year, d_month = date[0], date[1]
            month_start = tuple([d_year, d_month, 1] + [0 for _ in date[3:]])
            d_month = d_month + 1
            if d_month > 12:
                d_year += 1
                d_month = 1
            month_end = tuple([d_year, d_month, 1] + [0 for _ in date[3:]])
            return month_start, month_end

        def relative_day(week_start, which_day):
            d_year, d_doy = week_start[0], week_start[-2]
            doy = d_doy + which_day
            if doy < 1:
                d_year -= 1
                doy += 365 + int (calendar.isleap (d_year))
            elif doy > 365 + int (calendar.isleap (d_year)):
                doy -= 365 + int (calendar.isleap (d_year))
                d_year += 1
            day = time.strptime (str(d_year) + str(doy), "%Y%j")
            return day

        def stamp_dow (stamp):
            return time.localtime(stamp)[6]

        def stamp_floattime (stamp):
            t = time.localtime(stamp)
            return t[3] + t[4]/60.0

        DIV = 4

        def round_begin (x):
            import math
            return math.floor (x * DIV) / float (DIV)

        def round_end (x):
            import math
            return math.ceil (x * DIV) / float (DIV)

        try:
            date = time.strptime(req.args['date'],"%Y%m%d")
        except:
            date = time.localtime ()

        cweek = [[] for _ in xrange(7)]
        week_range = get_week(date)
        bg, en = time.mktime(week_range[0]), time.mktime(week_range[1])
        for ev in Event.events_between (self.env, bg, en,req.authname):
            begin = max (bg, ev.get_time_begin ())
            end = min (en, ev.get_time_end ()) - 1
            for d in xrange(stamp_dow(begin), stamp_dow(end)+1):
                cweek[d].append(ev)

        week_start = week_range[0]

        day_layouts = [cal_layout.layout (evts, round_begin, round_end)
                       for evts in cweek]

        for d in xrange (len (day_layouts)):
            today = relative_day(week_start, d)
            today_stamp = time.mktime (today)
            tomorrow_stamp = today_stamp + 24 * 60 * 60

            req.hdf['azcalendar.events.%d.date.year' % d] = today[0]
            req.hdf['azcalendar.events.%d.date.month' % d] = today[1]
            req.hdf['azcalendar.events.%d.date.day' % d] = today[2]
            for l in xrange (len (day_layouts[d])):
                for ev in day_layouts[d][l]:
                    begin = ev.get_time_begin ()
                    if begin < today_stamp:
                        begin = 0.0
                    else:
                        begin = round_begin (stamp_floattime (begin))

                    end = ev.get_time_end ()
                    if end >= tomorrow_stamp:
                        end = 24.0
                    else:
                        end = round_end (stamp_floattime (end))

                    base = 'azcalendar.events.%d.events.%d.%d' % (d, l, ev.get_id ())

                    req.hdf[base + '.id'] = ev.get_id ()
                    req.hdf[base + '.title'] = ev.get_title ()
                    req.hdf[base + '.priority'] = str(EventPriority[ev.get_priority ()])
                    req.hdf[base + '.brd_begin'] = int (round (begin * DIV))
                    req.hdf[base + '.brd_end'] = int (round (end * DIV))

                    if ev.get_time_begin () < today_stamp or ev.get_time_end () > tomorrow_stamp:
                        fmt = "%d.%m.%Y %H:%M"
                    else:
                        fmt = "%H:%M"
                    req.hdf[base + '.time_begin'] = time.strftime (fmt, time.localtime (ev.get_time_begin()))
                    req.hdf[base + '.time_end'] = time.strftime (fmt, time.localtime (ev.get_time_end()))

        display_months = []
        dm_year, dm_month = get_month (week_start)[0][:2]

        prev_year, prev_month, prev_day = date[:3]
        prev_month -= 1
        if prev_month < 1:
            prev_month += 12
            prev_year -= 1
        prev_day = min (calendar.monthrange (prev_year, prev_month)[1], prev_day)

        next_year, next_month, next_day = date[:3]
        next_month += 1
        if next_month > 12:
            next_month -= 12
            next_year += 1
        next_day = min (calendar.monthrange (next_year, next_month)[1], next_day)

        for i in range(3):
            month_range = get_month (tuple([dm_year, dm_month, 1] + [0 for i in range(6)]))
            interesting_days = {}

            bg, en = time.mktime(month_range[0]), time.mktime(month_range[1])
            evts = Event.events_between (self.env, bg, en, req.authname)

            for ev in evts:
                begin = ev.get_time_begin()
                if begin < bg:
                    begin = 1
                else:
                    begin = time.localtime(begin)[2]

                end = ev.get_time_end()
                if end > en:
                    end = calendar.monthrange(dm_year, dm_month)[1]
                else:
                    end = time.localtime(end)[2]

                priority = ev.get_priority()

                # Mark interesting days.
                for day in range (begin, end + 1):
                    if day not in interesting_days or interesting_days[day] < priority:
                        interesting_days[day] = priority

            interesting_days_l = [(day, str(EventPriority[interesting_days[day]]))
                                  for day in interesting_days.keys()]
            display_months.append ((dm_month - 1, dm_year, interesting_days_l))

            dm_month += 1
            if dm_month > 12:
                dm_year += 1
                dm_month = 1

        req.hdf['azcalendar.prev_date'] = "%04d%02d%02d" % (prev_year, prev_month, prev_day)
        req.hdf['azcalendar.today_date'] = time.strftime ("%Y%m%d")
        req.hdf['azcalendar.next_date'] = "%04d%02d%02d" % (next_year, next_month, next_day)

        for m in xrange (len (display_months)):
            month, year, impdays = display_months[m]
            _, numdays = calendar.monthrange (year, month + 1)
            firstday = calendar.weekday(year, month + 1, 1)

            req.hdf['azcalendar.months.%d.month' % m] = month
            req.hdf['azcalendar.months.%d.year' % m] = year
            req.hdf['azcalendar.months.%d.firstday' % m] = firstday
            req.hdf['azcalendar.months.%d.numdays' % m] = numdays

            for d in xrange (len (impdays)):
                day, priority = impdays[d]
                req.hdf['azcalendar.months.%d.impdays.%d' % (m, day)] = priority

        req.hdf['azcalendar.div'] = str(DIV)
        req.hdf['title'] = "Calendar"
        add_stylesheet (req, 'hw/css/azcalendar.css')
        return 'azcalendar.cs', None

    def process_delete(self, req):
        if req.args.has_key('id'):
            import re
            xid = req.args['id']
            if not re.match (r"[0-9]+", xid):
                return self.process_invalid(req)
            evt = Event.get_event(self.env,req.args['id'])
            evt.delete(self.env)

        return self.process_show(req)

    def process_event(self, req):
        add_stylesheet (req, 'hw/css/azcalendar.css')
        if req.method == 'GET' and req.args.has_key('id'):
            evt = Event.get_event(self.env,req.args['id'])
            req.hdf['azcalendar.evid'] = req.args['id']
            req.hdf['azcalendar.title'] = evt.get_title()
            req.hdf['azcalendar.author'] = evt.get_author()
            req.hdf['azcalendar.time_begin'] = time.strftime("%Y/%m/%d %H:%M",time.localtime(evt.get_time_begin()))
            req.hdf['azcalendar.time_end'] = time.strftime("%Y/%m/%d %H:%M",time.localtime(evt.get_time_end()))
            req.hdf['azcalendar.event.'+str(EventType[evt.get_type()])] = 1
            req.hdf['azcalendar.priority.'+str(EventPriority[evt.get_priority()])] = 1
            req.hdf['azcalendar.last_update'] = time.strftime("%Y/%m/%d %H:%M:%S",time.localtime(evt.get_time_update()))
            return 'azevent.cs', None

        elif req.method == 'GET' and req.args.has_key('update_event'):
            begin_time, end_time, begin_stamp, end_stamp \
              = caltools.parse_time_begin_end(req.args['time_begin'], req.args['time_end'])

            evt = Event.get_event(self.env,req.args['evid'])
            #evt.set_author(req.authname)
            evt.set_type(req.args['type'])
            evt.set_priority(req.args['priority'])
            evt.set_time_update(int(time.time()))
            evt.set_time_begin(begin_stamp)
            evt.set_time_end(end_stamp)
            evt.set_title(req.args['title'])
            date = time.strftime("%Y%m%d", begin_time)
            req.hdf['redir_url'] = str(self.env.href.azcalendar()) + "?date=%s" % date
            return evt.update(self.env, req)

        elif req.method == 'GET' and req.args.has_key('delete_event'):
            begin_time, end_time, begin_stamp, end_stamp \
              = caltools.parse_time_begin_end(req.args['time_begin'], req.args['time_end'])

            evt = Event.get_event(self.env,req.args['evid'])
            date = time.strftime("%Y%m%d", begin_time)
            req.hdf['redir_url'] = str(self.env.href.azcalendar()) + "?date=%s" % date
            return evt.delete(self.env)

    def process_invalid(self, req):
        add_stylesheet (req, 'hw/css/azcalendar.css')
        req.hdf['title'] = "Calendar: Error"
        req.hdf['azcalendar.reason'] = "Invalid request."
        return 'azerror.cs', None

    def process_request(self, req):
        KEY = "/azcalendar"
        query = req.path_info[req.path_info.index (KEY):]

        import re
        if not re.match ("%s(/add|/delete|/event)?($|\?.*)" % KEY, query):
            return self.process_invalid(req)
        elif KEY + "/add" in query:
            return self.process_add(req)
        elif KEY + "/delete" in query:
            return self.process_delete(req)
        elif KEY + "/event" in query:
            return self.process_event(req)
        else:
            return self.process_show(req)


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
        return [('hw', resource_filename(__name__, 'htdocs'))]


    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        """Called when a new Trac environment is created."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Insert a global version flag
        cursor.execute("INSERT INTO system (name,value) "
                       "VALUES ('azcalendar_version',%s)", (schema_version,))

        # Create the required tables
        for table in schema:
            for stmt in schema_to_sql(self.env, db, table):
                cursor.execute(stmt)

        db.commit()

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.

        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='azcalendar_version'")
        row = cursor.fetchone()
        if not row or int(row[0]) < schema_version:
            return True
        else:
            return False

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.

        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='azcalendar_version'")
        row = cursor.fetchone()
        if not row:
            self.environment_created()
        else:
            current_version = int(row[0])
            import upgrade
            for version in range(current_version + 1, schema_version + 1):
                for function in upgrade.map.get(version):
                    print textwrap.fill(inspect.getdoc(function))
                    function(self.env, db)
                    print 'Done.'
            cursor.execute("UPDATE system SET value=%s WHERE "
                           "name='azcalendar_version'", (schema_version,))
            self.log.info('Upgraded Aztech Calendar tables from version %d to %d',
                          current_version, schema_version)


    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = [('CAL_ADMIN', ('CAL_EDIT',)), ('CAL_EDIT', ('CAL_VIEW',)), 'CAL_VIEW']
        return actions
