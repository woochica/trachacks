# -*- coding: utf_8 -*-
#
# Copyright (C) 2013 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import time
from datetime import datetime, date, timedelta

from genshi.builder import tag

from trac.core import Component, implements
from trac.mimeview.api import Context
from trac.ticket.model import Ticket, Milestone
from trac.ticket.query import Query, QueryModule
from trac.ticket.web_ui import TicketModule
from trac.util.compat import any
from trac.util.datefmt import parse_date, utc
from trac.util.text import empty
from trac.web.api import IRequestHandler, IRequestFilter
from trac.web.chrome import (
    ITemplateProvider, INavigationContributor, Chrome, add_stylesheet,
    add_script, add_ctxtnav, add_script_data,
)
from trac.wiki.api import IWikiMacroProvider, parse_args

try:
    from babel import Locale
    from babel.core import LOCALE_ALIASES, UnknownLocaleError
    from babel.dates import get_day_names, get_month_names, format_date
except ImportError:
    LOCALE_ALIASES = {}
    def get_day_names(width=None, context=None, locale=None):
        names = dict()
        for day in range(0, 7):
            dt = datetime(2001, 1, day + 1)
            names[day] = dt.strftime('%a')
        return names
    def get_month_names(width=None, context=None, locale=None):
        names = dict()
        for m in range(1, 13):
            dt = datetime(2001, m, 1)
            names[m] = dt.strftime('%B')
        return names
    def format_date(date=None, format=None, locale=None):
        return str(date)


from ticketcalendar.api import (
    _, tag_, N_, gettext, add_domain, TEXTDOMAIN,
    Option, IntOption, ListOption,
)


# Utility functions

def _get_month_name(date, loc):
    m = date.month
    return get_month_names('wide', locale=loc)[m]

def _getdate(d, tz):
    try:
        if d.tzinfo is tz:
            return d.date()
        # Convert self to UTC, and attach the new time zone object.
        utc = (d - d.utcoffset()).replace(tzinfo=tz)
        # Convert from UTC to tz's local time.
        return tz.fromutc(utc).date()
    except:
        return None

def _parse_month_arg(string):
    if string:
        try:
            tt = time.strptime(string, '%Y-%m')
            return date(*tt[:3])
        except:
            pass
    return datetime.now().date().replace(day=1)

def _parse_duration_arg(arg):
    default = datetime.now(utc).date(), 7
    if not arg or '/P' not in arg:
        return default
    start, period = arg.split('/P', 1)
    try:
        start = parse_date(start, tzinfo=utc)
    except:
        start = None
    if not start:
        return default
    start = start.date()
    if period.endswith('D'):
        try:
            period = int(period[:-1])
        except:
            period = 0
        if period > 0:
            return start, period
    return default


"""
Output html data for Ticket calendar.
"""
class TicketCalendar(object):
    def __init__(self, env, req):
        self.env = env
        self.config = env.config
        self.log = env.log
        self.req = req
        self.mod = mod = TicketCalendarModule(env)
        self._priority_colors = self._prepare_list('priority',
                                                   mod.priority_colors)
        self._ticket_type_icons = self._prepare_list('ticket_type',
                                                     mod.ticket_type_icons)

    @classmethod
    def build_query_string(cls, constraints):
        args = []
        for idx, c in enumerate(constraints):
            if idx != 0:
                args.append(('or', empty))
            for key, val in c.iteritems():
                if isinstance(val, (list, tuple)):
                    val = '|'.join(val)
                args.append((key, val))
        def to_pair(key, val):
            if val is empty:
                return key
            return key + '=' + val
        return '&'.join(to_pair(key, val) for key, val in args)

    def get_priority_color(self, name):
        return self._priority_colors.get(name, '#fca89e')

    def get_ticket_type_icon(self, name):
        return self._ticket_type_icons.get(name, 'ui-icon-contact')

    def _prepare_list(self, type, values):
        values = filter(None, values)
        if not values:
            return {}
        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute('SELECT name FROM enum WHERE type=%s'
                       ' ORDER BY value',
                       (type,))
        names = [row[0] for row in cursor]
        cycle = []
        data = {}
        for idx, value in enumerate(values):
            value = value.strip()
            if not value:
                continue
            if ':' in value:
                name, value = value.split(':', 1)
                name = name.strip()
                value = value.strip()
                data[name] = value
                if name in names:
                    names.remove(name)
            else:
                cycle.append(value)
        data.update((name, cycle[idx % len(cycle)])
                    for idx, name in enumerate(names))
        return data

    def _get_href(self, name, query, kwargs):
        name = 'ticketcalendar-' + name
        args = []
        for idx, c in enumerate(query.constraints):
            if idx != 0:
                args.append(('or', empty))
            args.extend(c.iteritems())
        args.append(('order', query.order))
        if query.desc:
            args.append(('desc', 1))
        args.extend(kwargs.iteritems())
        return self.req.href(name, args)

    def get_list_href(self, query, start=None, period=7):
        kwargs = {}
        if start is not None:
            kwargs['_duration'] = '%s/P%dD' % (start.strftime('%Y-%m-%d'), period)
        return self._get_href('list', query, kwargs)

    def get_box_href(self, query, month=None):
        kwargs = {}
        if month:
            kwargs['_month'] = month.strftime('%Y-%m')
        return self._get_href('box', query, kwargs)

    @property
    def default_query(self):
        return self.config.get('query', 'default_query')

    @property
    def default_anonymous_query(self):
        return self.config.get('query', 'default_anonymous_query')

    def _create_milestone_item(self, milestone):
        icon = tag.span(tag.span('', class_='ui-icon %s' %
                                            self.mod.milestone_icon or ''),
                        class_='ui-icon-w')
        anchor = tag.a(milestone.name,
                       href=self.req.href('milestone', milestone.name))
        item = tag.li(icon, anchor,
                      style='background-color: %s;' %
                            self.mod.milestone_background_color,
                      class_='milestone')
        return item

    def _create_ticket_item(self, t):
        req = self.req
        style = None
        tktid = t.get('id')
        background = self.get_priority_color(t.get('priority'))
        if background:
            style = 'background-color: %s' % background
        item = tag.li(title='#%d %s' % (t.get('id'), t.get('summary')),
                      style=style,
                      data_href=req.href('ticketcalendar-ticket', id=tktid))

        for key, icon_class in (('_begin', 'arrowthick-1-e'),
                                ('_end',   'arrowthick-1-w')):
            if t.get(key):
                class_ = 'ui-icon ui-icon-' + icon_class
                item(tag.span(tag.span('', class_=class_), class_='ui-icon-w'))

        if t.get('_beginend'):
            item(tag.span(u'\u2666',
                          style='display: inline-block; margin: 0 0.4em;'))

        icon = self.get_ticket_type_icon(t.get('type'))
        if icon:
            item(tag.span(tag.span('', title=t.get('type'),
                                   class_ = 'ui-icon %s' % icon),
                          class_ = 'ui-icon-w'))
        else:
            item(tag.span(t.get('type'), class_='type'))

        item(tag.span(tag.a('#%d' % tktid,
                            href=req.href('ticket', tktid),
                            class_='open-ticketcalendar-ticket-detail %s' %
                                   t.get('status')),
                      u'\u00a0',
                      t.get('summary')))

        return item

    def _get_cols(self):
        cols = ['id','time','status','summary','priority',
                'milestone','owner','type','description']
        cols.extend(name
                    for name in set((self.mod.start_date_name,
                                     self.mod.due_date_name))
                    if name not in cols)
        return cols

    def _set_no_paginator(self, query):
        query.max = 0
        query.has_more_pages = False
        query.offset = 0
        query.group = None

    def get_query_from_string(self, qstring):
        query = Query.from_string(self.env, qstring)
        self._set_no_paginator(query)
        return query

    def get_constraints(self, arg_list=[]):
        return QueryModule(self.env)._get_constraints(self.req, arg_list)

    def get_query(self, constraints=None, args=None):
        req = self.req
        if not args:
            args = req.args
        if not constraints:
            # If no constraints are given in the URL, use the default ones.
            if req.authname and req.authname != 'anonymous':
                qstring = self.default_query
                user = req.authname
            else:
                email = req.session.get('email')
                name = req.session.get('name')
                qstring = self.default_anonymous_query
                user = email or name or None

            query = Query.from_string(self.env, qstring)
            args = {'order': query.order, 'col': query.cols, 'max': 0}
            constraints = query.constraints

            # Substitute $USER, or ensure no field constraints that depend
            # on $USER are used if we have no username.
            for clause in constraints:
                for field, vals in clause.items():
                    for (i, val) in enumerate(vals):
                        if user:
                            vals[i] = val.replace('$USER', user)
                        elif val.endswith('$USER'):
                            del clause[field]
                            break

        query = Query(self.env, args.get('report'), constraints,
                      self._get_cols(), args.get('order'), args.get('desc'))
        self._set_no_paginator(query)
        return query

    def template_data(self, req, query, kwargs=None):
        db = self.env.get_read_db()
        tickets = query.execute(req, db)
        context = Context.from_request(req, 'query')
        return query.template_data(context, tickets, None, datetime.now(utc),
                                   req)

    def gen_calendar(self, tickets, query, month, width=None, nav=True):
        milestones = self._get_milestones()

        req = self.req
        locale = self._get_locale()
        first_week_day = self._get_first_week_day(locale)
        start_date_format = self.mod.start_date_format
        due_date_format = self.mod.due_date_format

        if not month:
            month = datetime.now(req.tz)
            month = datetime(month.year, month.month, 1).date()

        # init data
        today = datetime.now(req.tz).date()

        # generate calendar data
        weeks = self._get_month_calendar(month.year, month.month,
                                         first_week_day, locale)
        days = sorted(sum(weeks, []))
        tickets = self._filter_tickets(days, tickets, req.tz)
        milestones = self._filter_milestones(days, milestones, req.tz)
        cal = [[{'date': day,
                 'tickets': tickets[day], 'milestones': milestones[day]}
                for day in week]
               for week in weeks]

        def genli(t):
            if isinstance(t, Milestone):
                return self._create_milestone_item(t)
            else:
                return self._create_ticket_item(t)

        def gentd(week_idx, day_info):
            day = day_info['date']
            tt = day_info['milestones'] + day_info['tickets']
            if len(tt) < 6:
                ttshow = tt
                ttall = []
            else:
                ttshow = tt[:4]
                ttall = tt

            tdclass = []
            if day == today:
                tdclass.append('today')
            if day.weekday() in (5, 6):
                tdclass.append('weekend')

            formatted_day = format_date(day, format='long', locale=locale)

            td = tag.td(
                class_=' '.join(tdclass),
                data_for_start_date=day.strftime(start_date_format),
                data_for_due_date=day.strftime(due_date_format),
                data_fdate=formatted_day)

            label = []
            if day == today:
                label.append(tag.span(_("Today"), class_='today'))
            label.append(tag.span(unicode(day.day),
                                  class_=('day normal', 'day')[day == today]))
            td(tag.div(label))
            if ttshow:
                td(tag.ul([genli(t) for t in ttshow]))

            if ttall:
                id = 'calendar-more-%s' % str(day)
                td(tag.a(_("%d more tickets...") % (len(ttall) - 4),
                         href='#' + id,
                         class_='show-all-list'),
                   tag.div(tag.h4(formatted_day),
                           tag.ul([genli(t) for t in ttall]),
                           class_='ticketcalendar-popup-list',
                           id=id,
                           data_title=format_date(day, locale=locale,
                                                  format='full')))

            return td

        day_names = get_day_names(locale=locale, width='abbreviated')
        day_names = [day_names[(idx + first_week_day) % 7]
                     for idx in xrange(7)]

        header = tag.div(class_='ticketcalendar-header')
        if nav:
            def nav_href(d):
                return self.get_box_href(query, d)

            def nav_pager(d):
                return tag.span(
                    tag.a(u'\u25c4', href=nav_href(d - timedelta(days=1))),
                    tag.a(_("Current month"), href=nav_href(date.today())),
                    tag.a(u'\u25ba', href=nav_href(d + timedelta(days=31))),
                    class_='ticketcalendar-pager')

            def nav_macro():
                macro = (
                    '[[TicketCalendar(type=box,month=%(month)s,'
                    'query=%(query)s,order=%(order)s%(extra)s)]]' %
                    (dict(month=month.strftime('%Y-%m'),
                          query=self.build_query_string(query.constraints),
                          order=query.order,
                          extra=query.desc and ',desc=1' or '')))
                text = tag.input(type='text', readonly='readonly', size='80',
                                 value=macro, style='width:0;display:none')
                return tag.span(_("Macro"), text,
                                class_='ticketcalendar-macro')

            header(tag.div(nav_macro(), nav_pager(month),
                           class_='ticketcalendar-nav'))

        header(tag.h4(_("%(month_name)s, %(year)s",
                        month_name=_get_month_name(month, locale),
                        year=month.year)))

        calendar = tag.table(
             tag.thead(tag.tr(tag.th(name) for name in day_names)),
             tag.tbody([tag.tr([gentd(idx, d) for d in w])
                               for idx, w in enumerate(cal)]),
             class_='calendar')

        can_create = 'TICKET_CREATE' in req.perm

        ticket_box = tag.div(
            tag.h4(tag.span('', class_='tc-today-date')),
            tag.ul(
                tag.li(tag.a(
                    tag_("New ticket with \"%(date)s\" as the start date",
                         date=tag.span('', data='start-date')),
                    data_href=req.href('newticket',
                                       [(self.mod.start_date_name, '')]),
                    class_='newticket-start-date')),
                tag.li(tag.a(
                    tag_("New ticket with \"%(date)s\" as the due date",
                         date=tag.span('', data='due-date')),
                    data_href=req.href('newticket',
                                       [(self.mod.due_date_name, '')]),
                    class_='newticket-due-date'))),
            title=_("Create new ticket"),
            class_='ticketcalendar-newticket-box',
            style='display:none',
            data_writable=(None, 'writable')[can_create])

        class_ = ('ticketcalendar',
                  'ticketcalendar ticketcalendar-can-create')[can_create]
        return tag.div(header, calendar, ticket_box, class_=class_,
                       style=width and ('width: %s' % width) or None)

    def get_list_events(self, tickets, start_date, period):
        milestones = self._get_milestones()

        req = self.req
        if not start_date or not period:
            start_date = date.today()
            period = 7
        locale = self._get_locale()

        days = [start_date + timedelta(days=i) for i in xrange(period)]
        tickets = self._filter_tickets(days, tickets, req.tz)
        milestones = self._filter_milestones(days, milestones, req.tz)

        events = [{'date': day,
                   'formatted_date': format_date(day, format='full',
                                                 locale=locale),
                   'tickets': tickets[day], 'milestones': milestones[day]}
                  for day in days]

        return events

    def render_list(self, tickets, start_date, period):
        events = self.get_list_events(tickets, start_date, period)
        data = {}
        data['ticketcalendar'] = {
            'events': events,
            'last_week': None,
            'next_week': None,
            'create_ticket': self._create_ticket_item,
            'create_milestone': self._create_milestone_item,
        }
        return Chrome(self.env).render_template(
            self.req, 'ticketcalendar_list.html', data, None, fragment=True)

    def _filter_tickets(self, days, tickets, tzinfo):
        get_start_date = self.mod.get_start_date
        get_due_date = self.mod.get_due_date
        result = dict((day, []) for day in days)

        for ticket in tickets:
            begin = get_start_date(ticket)
            if begin is None:
                begin = _getdate(ticket.get('time'), tzinfo)
            end = get_due_date(ticket)

            if begin == end:
                if begin in result:
                    copied = ticket.copy()
                    copied['_beginend'] = True
                    result[begin].append(copied)
            else:
                if begin in result:
                    copied = ticket.copy()
                    copied['_begin'] = True
                    result[begin].append(copied)
                if end in result:
                    copied = ticket.copy()
                    copied['_end'] = True
                    result[end].append(copied)

        return result

    def _filter_milestones(self, days, milestones, tzinfo):
        rv = dict((day, []) for day in days)
        for milestone in milestones:
            if not milestone.due:
                continue
            due = _getdate(milestone.due, tzinfo)
            if due in rv:
                rv[due].append(milestone)
        return rv

    def _get_locale(self):
        locale = self.req.locale
        if not locale:
            return locale

        if not locale.territory:
            # search first locale which has the same `langauge` and territory
            # in preferred languages
            for l in self.req.languages:
                l = l.replace('-', '_').lower()
                if l.startswith(locale.language.lower() + '_'):
                    try:
                        l = Locale.parse(l)
                        if l.territory:
                            locale = l
                            break
                    except UnknownLocaleError:
                        pass
            if not locale.territory and locale.language in LOCALE_ALIASES:
                locale = Locale.parse(LOCALE_ALIASES[locale.language])

        return locale or Locale('en', 'US')

    def _get_first_week_day(self, locale):
        first = self.mod.first_week_day
        if first not in xrange(0, 7):
            if locale:
                first = locale.first_week_day
            else:
                first = 0  # Monday
        return first

    def _get_month_calendar(self, year, month, first_week_day, locale):
        base = date(year, month, 1)
        base -= timedelta(days=(base.weekday() - first_week_day) % 7)
        days = []
        for week in xrange(6):
            first = base + timedelta(days=week * 7)
            last = first + timedelta(days=6)
            if first.month != month and last.month != month:
                break
            days.append([first + timedelta(days=i) for i in xrange(7)])
        return days

    def _get_milestones(self):
        return Milestone.select(self.env, include_completed=False)


class TicketCalendarModule(Component):

    implements(ITemplateProvider, IRequestHandler, IRequestFilter,
               INavigationContributor, IWikiMacroProvider)

    milestone_background_color = Option(
        'ticketcalendar', 'milestone.background-color', default='#c2c2c2',
        doc=N_("The background color for milestones"))

    milestone_icon = Option(
        'ticketcalendar', 'milestone.icon', default='ui-icon-flag',
        doc=N_("The icon name in jquery-ui for milestones. See http://jquery-"
               "ui.googlecode.com/svn/tags/1.8.21/tests/static/icons.html."))

    priority_colors = ListOption(
        'ticketcalendar', 'ticket.priority.color',
        default='#fca89e, #ffad46, #7bd148, #8db3f0, #cca6ac',
        doc=N_("""\
Comma-separated list of background colors to use for the ticket priorities. \
It can be specified explicitly pairs of priority name and background color. \
e.g. `blocker:#fa6653, critical:#ffad46, ...`."""))

    ticket_type_icons = ListOption(
        'ticketcalendar', 'ticket.type.icon',
        default='ui-icon-contact, ui-icon-lightbulb, ui-icon-check, '
                'ui-icon-gear, ui-icon-comment',
        doc=N_("""\
Comma-separated list of icon names in jquery-ui to use for ticket types.
See http://jquery-ui.googlecode.com/svn/tags/1.8.21/tests/static/icons.html.

It can be specified explicitly pairs of ticket type and icon name.
e.g. `defect:ui-icon-contact, task:ui-icon-lightbulb, ...`."""))

    first_week_day = IntOption(
        'ticketcalendar', 'first_week_day', default=-1,
        doc=N_("The first day of the week in calendar. If -1, use first week "
               "day in user's locale. Otherwise, use the specified number "
               "(0 is Monday as the first day of the week)."))

    start_date_name = Option(
        'ticketcalendar', 'ticket.start_date', default='start_date',
        doc=N_("The field name for start date of ticket"))

    _start_date_format = Option(
        'ticketcalendar', 'ticket.start_date.format', default='%Y/%m/%d',
        doc=N_("The format for start date of ticket"))

    due_date_name = Option(
        'ticketcalendar', 'ticket.due_date', default='due_date',
        doc=N_("The field name for due date of ticket"))

    _due_date_format = Option(
        'ticketcalendar', 'ticket.due_date.format', default='%Y/%m/%d',
        doc=N_("The format for due date of ticket"))

    def __init__(self):
        from pkg_resources import resource_filename, resource_isdir
        if resource_isdir(__name__, 'locale'):
            locale_dir = resource_filename(__name__, 'locale')
            add_domain(self.env.path, locale_dir)

    @property
    def start_date_format(self):
        return self._start_date_format.encode('utf-8')

    @property
    def due_date_format(self):
        return self._due_date_format.encode('utf-8')

    def get_start_date(self, ticket):
        return self._getdate(ticket.get(self.start_date_name),
                             self.start_date_format)

    def get_due_date(self, ticket):
        return self._getdate(
                ticket.get(self.due_date_name)
                , self.due_date_format)

    def _getdate(self, d, format='%d/%m/%Y'):
        if isinstance(d, int):
            return date.fromtimestamp(d).date()
        elif isinstance(d, basestring):
            try:
                tt = time.strptime(d, format)
                return date(*tt[0:3])
            except ValueError:
                return None
        else:
            return None

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if (template and template.endswith('.html') and
            any(template.startswith(prefix)
                for prefix in ('wiki_', 'roadmap', 'milestone_'))):
            self._add_header_contents(req)
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ticketcalendar', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'ticketcalendar-box'

    def get_navigation_items(self, req):
        if 'TICKET_VIEW' in req.perm:
            anchor = tag.a(_("Ticket Calendar"),
                           href=req.href('ticketcalendar-box'))
            yield ('mainnav', 'ticketcalendar-box', anchor)

    # IWikiMacroProvider methods

    def get_macros(self):
        return ['TicketCalendar']

    _macro_description = N_("""\
Display tickets and milestones in calendar or list view.

Usage:
{{{
[[TicketCalendar(type=box,query=status!=closed,month=2013-05)]]
[[TicketCalendar(type=list,query=status!=closed,duration=2013-05-16/P7D)]]
}}}

 * The `type` parameter determines how the tickets and milestones are presented:
   - `box`: display in calendar view (default)
   - `list`: display in list view
 * The `query` parameter is used to query the tickets to display.
 * The `month` parameter can be specified as `YYYY-MM` in only calendar view,
   The default is current month.
 * The `duration` parameter can be specified as `YYYY-MM-DD/PnD` in only list
   view. The default is today and 7 days.
""")

    def get_macro_description(self, name):
        from trac.wiki.macros import WikiMacroBase
        if hasattr(WikiMacroBase, '_domain'):
            return TEXTDOMAIN, self._macro_description
        else:
            return gettext(self._macro_description)

    def is_inline(self, content):
        return False

    def expand_macro(self, formatter, name, arguments):
        req = formatter.req
        calendar = TicketCalendar(self.env, req)
        args, kwargs = parse_args(arguments, strict=False)
        query = kwargs.get('query')
        if query:
            query = calendar.get_query_from_string(query)
        else:
            query = calendar.get_query(args=kwargs)
        data = calendar.template_data(req, query, kwargs)
        width = kwargs.get('width')

        if kwargs.get('type') == 'list':
            start, period = _parse_duration_arg(kwargs.get('duration'))
            return calendar.render_list(data['tickets'], start, period)
        else:
            month = _parse_month_arg(kwargs.get('month'))
            return calendar.gen_calendar(data['tickets'], query, month, width,
                                         nav=False)

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info in ('/ticketcalendar-box',
                                 '/ticketcalendar-list',
                                 '/ticketcalendar-ticket')

    def process_request(self, req):
        req.perm.assert_permission('TICKET_VIEW')
        req.send_header('X-UA-Compatible', 'IE=edge')

        if req.path_info == '/ticketcalendar-ticket':
            return self._process_ticket_detail(req)

        self._add_header_contents(req)

        calendar = TicketCalendar(self.env, req)
        query = calendar.get_query(calendar.get_constraints())
        data = calendar.template_data(req, query)
        data['query_form_filters'] = self._render_query_form_filters(req, data)
        properties = dict((name, dict((key, field[key])
                                      for key in ('type', 'label', 'options',
                                                  'optgroups')
                                      if key in field))
                          for name, field in data['fields'].iteritems())
        add_script_data(req, {'properties': properties,
                              'modes': data['modes']})
        redirect = 'update' in req.args

        if req.path_info == '/ticketcalendar-box':
            month = _parse_month_arg(req.args.get('_month'))
            if redirect:
                req.redirect(calendar.get_box_href(query, month))
            return self._process_box(req, query, data, month)

        if req.path_info == '/ticketcalendar-list':
            start, period = _parse_duration_arg(req.args.getfirst('_duration'))
            if redirect:
                req.redirect(calendar.get_list_href(query, start, period))
            return self._process_list(req, query, data, start, period)

    def _render_query_form_filters(self, req, data):
        if 'query_href' not in req.session:
            req.session['query_href'] = ''  # workaround crashing in batchmod
        fragment = Chrome(self.env).render_template(req, 'query.html', data,
                                                    None, fragment=True)
        return fragment.select('//fieldset[@id="filters"]')

    def _process_box(self, req, query, data, month):
        calendar = TicketCalendar(self.env, req)
        content = calendar.gen_calendar(data['tickets'], query, month)

        data['title'] = _('Ticket Calendar (Calendar view)')
        data['month'] = month.strftime('%Y-%m')
        data['content'] = content
        data['ticketcalendar'] = {'mode': 'calendar'}

        add_ctxtnav(req, _('Calendar view'))
        add_ctxtnav(req, _('List view'), calendar.get_list_href(query))

        return 'ticketcalendar_calendar.html', data, None

    def _process_list(self, req, query, data, start_date, period):
        calendar = TicketCalendar(self.env, req)
        events = calendar.get_list_events(data['tickets'], start_date, period)
        data['ticketcalendar'] = {
            'events': events,
            'last_week': calendar.get_list_href(query,
                                                start_date - timedelta(days=7),
                                                period + 7),
            'next_week': calendar.get_list_href(query, start_date, period + 7),
            'create_ticket': calendar._create_ticket_item,
            'create_milestone': calendar._create_milestone_item,
        }
        data['title'] = _('Ticket Calendar (List view)')
        data['macro'] = \
            '[[TicketCalendar(type=list,duration=%s,query=%s,order=%s%s)]]' % (
            '%s/P%dD' % (start_date.strftime('%Y-%m-%d'), period),
            calendar.build_query_string(query.constraints),
            query.order,
            query.desc and ',desc=1' or '')

        add_ctxtnav(req, _('Calendar view'),
                    calendar.get_box_href(query, date.today()))
        add_ctxtnav(req, _('List view'))

        return 'ticketcalendar_calendar.html', data, None

    def _process_ticket_detail(self, req):
        ticket = Ticket(self.env, int(req.args.get('id')))
        data = {'ticket': ticket,
                'fields': self._prepare_fields(req, ticket),
                'description_change': None,
                'can_append': None,
                'preview_mode': None,
                'writable': 'TICKET_CHGPROP' in req.perm or
                            'TICKET_APPEND' in req.perm or
                            'TICKET_MODIFY' in req.perm,
                }
        return 'ticketcalendar_ticket_detail.html', data, None

    def _add_header_contents(self, req):
        add_stylesheet(req, 'common/css/report.css')
        add_stylesheet(req, 'common/css/ticket.css')
        if hasattr(Chrome, 'add_jquery_ui'):
            Chrome(self.env).add_jquery_ui(req)
        else:
            add_stylesheet(req, 'ticketcalendar/css/jquery-ui.min.css')
        add_stylesheet(req, 'ticketcalendar/css/colorbox.css')
        add_stylesheet(req, 'ticketcalendar/css/ticketcalendar.css')
        add_script(req, 'common/js/folding.js')
        add_script(req, 'common/js/query.js')
        add_script(req, 'ticketcalendar/js/jquery.colorbox-min.js')
        add_script(req, 'ticketcalendar/js/jquery.balloon.min.js')
        add_script(req, 'ticketcalendar/js/ticketcalendar.js')

    def _prepare_fields(self, req, ticket):
        return TicketModule(self.env)._prepare_fields(req, ticket)
