#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# Copyright (C) 2005 Jan Finell <finell@cenix-bioscience.com>
# Copyright (C) 2007 Mike Comb <mcomb@mac.com>
# Copyright (C) 2008 JaeWook Choi <http://trac-hacks.org/wiki/butterflow>
# Copyright (C) 2008, 2009 W. Martin Borgert <debacle@debian.org>
# Copyright (C) 2010-2013 Steffen Hoffmann <hoff.st@shaas.net>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Matthew Good <trac@matt-good.net>

from babel import Locale, UnknownLocaleError
from babel.dates import format_datetime, get_day_names
from datetime import datetime, timedelta
from genshi.builder import tag
from genshi.core import escape, Markup
from pkg_resources import resource_filename
from sgmllib import SGMLParser

from trac.config import BoolOption, Configuration, Option
from trac.core import Component, implements
from trac.util.compat import any
from trac.util.datefmt import format_date
from trac.util.text import shorten_line, to_unicode
from trac.web.href import Href
from trac.web.chrome import add_stylesheet, ITemplateProvider
from trac.wiki.api import parse_args, IWikiMacroProvider, WikiSystem
from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase

from wikicalendar.api import add_domain, _, cleandoc_, gettext, tag_
from wikicalendar.ticket import WikiCalendarTicketProvider

uts = None
try:
    from trac.util.datefmt import to_utimestamp
    uts = "env with POSIX microsecond time stamps found"
except ImportError:
    # Fallback to old function for 0.11 compatibility.
    from trac.util.datefmt import to_timestamp

macro_doc_compat = False
try:
    WikiMacroBase._domain
except AttributeError:
    macro_doc_compat = True

_TRUE_VALUES = ('True', 'true', 'yes', 'y', '1')


__all__ = ['TextExtractor', 'WikiCalendarMacros']


class TextExtractor(SGMLParser):
    """A simple custom HTML-to-text parser without external dependencies.

    Taken from http://stackoverflow.com/questions/3398852
      /using-python-remove-html-tags-formatting-from-a-string/3399071#3399071
    by Wai Yip Tung.
    """
    def __init__(self):
        self.text = []
        SGMLParser.__init__(self)
    def handle_data(self, data):
        self.text.append(data)
    def getvalue(self):
        return ''.join(self.text)


class WikiCalendarMacros(Component):
    """Provides macros to display wiki page navigation in a calendar view."""

    implements(IWikiMacroProvider, ITemplateProvider)

    # Common [wikicalendar] section
    internal_css = BoolOption('wikicalendar', 'internal_css', False,
                              """Whether CSS should be embedded into the
                              HTML. This is meant as fallback, if linking
                              the external style sheet file fails.""")
    ticket_due = Option('wikicalendar', 'ticket.due_field', 'due_close',
                        doc="""Custom due date field name to evaluate
                        for displaying tickets by date.""")
    ticket_due_fmt = Option('wikicalendar', 'ticket.due_field.format',
                            '%y-%m-%d', doc="""Custom due date value format,
                            that is any expression supported by strftime or
                            'ts' identifier for POSIX microsecond time stamps
                            as supported in later Trac versions.""")

    # Old [wikiticketcalendar] section
    due_field_name = Option('wikiticketcalendar', 'ticket.due_field.name',
                            'due_close', doc = """Custom due date field name
                            to evaluate for displaying tickets by date.
                            (''depreciated - see wikicalendar section'')""")
    due_field_fmt = Option('wikiticketcalendar', 'ticket.due_field.format',
                           '%y-%m-%d', doc = """Custom due date value format,
                           that is any expression supported by strftime or
                           'ts' identifier for POSIX microsecond time stamps
                           as supported in later Trac versions.
                           (''depreciated - see wikicalendar section'')""")

    htdocs_path = resource_filename(__name__, 'htdocs')

    def __init__(self):
        # Bind 'wikicalendar' catalog to the specified locale directory.
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

        # Parse 'wikicalendar' configuration section for test instructions.
        # Valid options are written as check.<item>.<test name>, where item
        # is optional.  The value must be a SQL query with arguments depending
        # on the item it applies to.
        self.checks = {}
        conf_section = self.config['wikicalendar']
        for key, sql in conf_section.options():
            if key.startswith('check.'):
                check_type = key.split('.')
                if len(check_type) in range(2,4):
                    self.checks[check_type[-1]] = {'test': sql}
                    if len(check_type) == 3:
                        # We've got test type information too.
                        self.checks[check_type[-1]]['type'] = check_type[1]

        # Options in 'wikicalendar' configuration section take precedence over
        # those in old 'wikiticketcalendar' section.
        cfg = self.config
        if 'wikicalendar' in cfg.sections():
            # Rewrite option name for easier plugin upgrade.
            if cfg.has_option('wikicalendar', 'ticket.due_field.name'):
                self.env.log.debug("Old 'wikiticketcalendar' option found.")
                cfg.set('wikicalendar', 'ticket.due_field',
                      c.get('wikicalendar', 'ticket.due_field.name'))
                cfg.remove('wikicalendar', 'ticket.due_field.name')
                cfg.save()
                self.env.log.debug('Updated to new option: ticket.due_field')

            self.tkt_due_field = self.ticket_due
            self.tkt_due_format = self.ticket_due_fmt
        else:
            self.tkt_due_field = self.due_field_name
            self.tkt_due_format = self.due_field_fmt

    # ITemplateProvider methods

    # Returns additional path, where stylesheets are placed.
    def get_htdocs_dirs(self):
        return [('wikicalendar', self.htdocs_path)]

    # Returns additional path, where templates are placed.
    def get_templates_dirs(self):
        return []

    # IWikiMacroProvider methods

    # Returns list of provided macro names.
    def get_macros(self):
        yield 'WikiCalendar'
        yield 'WikiTicketCalendar'

    # Returns documentation for provided macros.
    def get_macro_description(self, name):

        # TRANSLATOR: Keep Trac style WikiFormatting here, please.
        cal_doc = cleandoc_(
            """Inserts a small calendar, where each day links to a wiki page,
            whose name matches the format set by `wiki`. The current day is
            highlighted, and days with a due Milestone are marked in bold.

            Usage:
            {{{
            [[WikiCalendar([year, month, nav, wiki, base=<page.name>)]]
            }}}

            Arguments (all optional, but positional - order matters):
             1. `year` (4-digit year), defaults to `*` (current year)
             1. `month` (2-digit month), defaults to `*` (current month)
             1. `nav` (boolean) - show previous/next navigation, defaults to
                `true`
             1. `wiki` (valid strftime expression) - page name format,
                defaults to `%Y-%m-%d`

            Keyword-only argument:
             * `base` (page name string) - create new pages from that
               template in PageTemplates, defaults to `''` (empty string)

            Examples:
            {{{
            [[WikiCalendar(2006,07)]]
            [[WikiCalendar(2006,07,false)]]
            [[WikiCalendar(*,*,true,Meeting-%Y-%m-%d)]]
            [[WikiCalendar(2006,07,false,Meeting-%Y-%m-%d)]]
            [[WikiCalendar(*,*,true,Meeting-%Y-%m-%d,base=MeetingNotes)]]
            }}}"""
        )

        tcal_doc = cleandoc_(
            """Display Milestones and Tickets in a calendar view.

            Days include links to:
             * all milestones, that are due on that day
             * all tickets, that are due on that day
             * all tickets created on that day (configurable)
             * one or more wiki pages with name matching the configured format
            preparing links for creating new wiki pages from a template too

            Usage:
            {{{
            [[WikiTicketCalendar(year, month, nav, wiki, cdate, base, query,
                                 short, width)]]
            }}}

            Arguments (all optional, but positional - order matters):
             1. `year` (4-digit year), defaults to `*` (current year)
             1. `month` (2-digit month), defaults to `*` (current month)
             1. `nav` (boolean) - show previous/next navigation, defaults to
                `true`
             1. `wiki` (valid strftime expression) - page name format,
                defaults to `%Y-%m-%d`
             1. `cdate` (boolean) - show tickets created on that day too,
                defaults to `true`
             1. `base` (page name string) - create new pages from that
                template in PageTemplates, defaults to `''` (empty string)
             1. `query` (valid TracQuery) - including expressions grouped by
                AND (OR since 0.12) for general ticket selection, defaults
                to `id!=0`
             1. `short` (integer) - total ticket count per day, that will have
                ticket list display condensed to just ticket numbers, defaults
                to `0` (never condense ticket list
             1. `width` (valid CSS size), prefixed `+` forces more, defaults
                to `100%;`

            Examples:
            {{{
            [[WikiTicketCalendar(2006,07)]]
            [[WikiTicketCalendar(2006,07,false)]]
            [[WikiTicketCalendar(*,*,true,Meeting-%Y-%m-%d)]]
            [[WikiTicketCalendar(2006,07,false,Meeting-%Y-%m-%d)]]
            [[WikiTicketCalendar(2006,07,true,*,true)]]
            [[WikiTicketCalendar(2006,07,true,Meeting-%Y-%m-%d,true,Meeting)]]
            }}}

            Equivalent keyword arguments are available for all but the first
            two arguments.

            Examples:
            {{{
            [[WikiTicketCalendar(wiki=Talk-%Y-%m-%d,base=Talk)]]
             same as [[WikiTicketCalendar(*,*,true,Talk-%Y-%m-%d,true,Talk)]]
            [[WikiTicketCalendar(wiki=Meeting-%Y-%m-%d,query=type=task)]]
            [[WikiTicketCalendar(wiki=Meeting_%Y/%m/%d,short=6)]]
            }}}

            Mixed use of both, simple and keyword arguments is possible, while
            order of simple arguments (see above) still applies and keyword
            arguments in-between do not count for positional argument mapping.

            Example:
            {{{
            [[WikiTicketCalendar(wiki=Meeting_%Y/%m/%d,*,*,true,width=+75%;)]]
            }}}

            Keyword-only argument:
             * `subpages` (list of page names separated by '|') - replace
               wiki page link per day with one link per sub-page labeled by
               first character of sub-page name, defaults to an empty list

            Example:
            {{{
            [[WikiTicketCalendar(wiki=Meetings_%Y/%m/%d,
                                 subpages=Morning|Afternoon)]]
            }}}"""
        )

        if name == 'WikiCalendar':
            if macro_doc_compat:
                # Optionally translated doc for Trac < 1.0.
                return gettext(cal_doc)
            return ('wikicalendar', cal_doc)
        elif name == 'WikiTicketCalendar':
            if macro_doc_compat:
                return gettext(tcal_doc)
            return ('wikicalendar', tcal_doc)

    # Returns macro content.
    def expand_macro(self, formatter, name, arguments):
        env = self.env
        tz = formatter.req.tz

        # Parse arguments from macro invocation.
        args, kwargs = parse_args(arguments, strict=False)

        # Find year and month of interest.
        year = formatter.req.args.get('year')
        # Not clicked on any previous/next button, next look for macro args.
        if not year and len(args) >= 1 and args[0] <> "*":
            year = args[0]
        year = year and year.isnumeric() and int(year) or None

        month = formatter.req.args.get('month')
        # Not clicked on any previous/next button, next look for macro args.
        if not month and len(args) >= 2 and args[1] <> "*":
            month = args[1]
        month = month and month.isnumeric() and int(month) or None

        now = datetime.now(tz)
        # Force offset from start-of-day to avoid a false 'today' marker,
        # but use it only on request of different month/year.
        now.replace(second=1)
        today = None
        if month and month != now.month:
            today = now.replace(month=month)
        if year and year != now.year:
            today = today and today.replace(year=year) or \
                    now.replace(year=year)
        # Use current month and year, if nothing else has been requested.
        if not today:
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        showbuttons = True
        if len(args) >= 3 or kwargs.has_key('nav'):
            try:
                showbuttons = kwargs['nav'] in _TRUE_VALUES
            except KeyError:
                showbuttons = args[2] in _TRUE_VALUES

        wiki_page_format = "%Y-%m-%d"
        if len(args) >= 4 and args[3] != "*" or kwargs.has_key('wiki'):
            try:
                wiki_page_format = str(kwargs['wiki'])
            except KeyError:
                wiki_page_format = str(args[3])
        # Support relative paths in macro arguments for wiki page links.
        wiki_page_format = _resolve_relative_name(wiki_page_format,
                                                  formatter.resource.id)

        list_condense = 0
        show_t_open_dates = True
        wiki_subpages = []

        # Read optional check plan.
        check = []
        if kwargs.has_key('check'):
            check = kwargs['check'].split('.')

        if name == 'WikiTicketCalendar':
            if len(args) >= 5 or kwargs.has_key('cdate'):
                try:
                    show_t_open_dates = kwargs['cdate'] in _TRUE_VALUES
                except KeyError:
                    show_t_open_dates = args[4] in _TRUE_VALUES

            # TracQuery support for ticket selection
            query_args = "id!=0"
            if len(args) >= 7 or kwargs.has_key('query'):
                # prefer query arguments provided by kwargs
                try:
                    query_args = kwargs['query']
                except KeyError:
                    query_args = args[6]
            provider = WikiCalendarTicketProvider(env)
            tickets = provider.harvest(formatter.req, query_args)

            # compress long ticket lists
            if len(args) >= 8 or kwargs.has_key('short'):
                # prefer query arguments provided by kwargs
                try:
                    list_condense = int(kwargs['short'])
                except KeyError:
                    list_condense = int(args[7])

            # control calendar display width
            cal_width = "100%;"
            if len(args) >= 9 or kwargs.has_key('width'):
                # prefer query arguments provided by kwargs
                try:
                    cal_width = kwargs['width']
                except KeyError:
                    cal_width = args[8]

            # multiple wiki (sub)pages per day
            if kwargs.has_key('subpages'):
                wiki_subpages = kwargs['subpages'].split('|')

        # Respect user's locale, if available.
        try:
            loc_req = str(formatter.req.locale)
        except AttributeError:
            # Available since Trac 0.12.
            loc_req = None
        loc = None
        if loc_req:
            try:
                 loc = Locale.parse(loc_req, sep='-')
            except UnknownLocaleError:
                # Re-try with system default.
                loc = Locale.default('LC_TIME')
            if not loc:
                loc = Locale('en', 'US')
            env.log.debug('Locale setting for wiki calendar: %s'
                          % loc.get_display_name('en'))

        # Prepare datetime objects for previous/next navigation link creation.
        prev_year = today.replace(year=today.year - 1)
        if today.month < 4:
            fr_month = today.replace(month=today.month + 9,
                                     year=today.year - 1)
        else:
            fr_month = today.replace(month=today.month - 3)
        if today.month == 1:
            prev_month = today.replace(month=12, year=today.year - 1)
        else:
            prev_month = today.replace(month=today.month - 1)
        if today.month == 12:
            next_month = today.replace(month=1, year=today.year + 1)
        else:
            next_month = today.replace(month=today.month + 1)
        if today.month > 9:
            ff_month = today.replace(month=today.month - 9,
                                     year=today.year + 1)
        else:
            ff_month = today.replace(month=today.month + 3)
        next_year = today.replace(year=today.year + 1)

        # Find first and last calendar day, probably in last/next month,
        # using exact start-of-day here.
        first_day_month = today.replace(day=1, second=0)
        isoweekday = int(format_datetime(first_day_month, 'c', locale=loc))
        first_day_cal = first_day_month - timedelta(isoweekday - 1)
        last_day_month = next_month.replace(day=1) - timedelta(1)
        isoweekday = int(format_datetime(last_day_month, 'c', locale=loc))
        last_day_cal = last_day_month + timedelta(7 - isoweekday)

        # Finally building the output now.
        # Begin with caption and optional navigation links.
        buff = tag.tr()

        if showbuttons is True:
            # Create calendar navigation buttons.
            nx = 'next'
            pv = 'prev'
            nav_pvY = _mknav(formatter, '&lt;&lt;', pv, prev_year, loc)
            nav_frM = _mknav(formatter, '&nbsp;&lt;', pv, fr_month, loc)
            nav_pvM = _mknav(formatter, '&nbsp;&laquo;', pv, prev_month, loc)
            nav_nxM = _mknav(formatter, '&raquo;&nbsp;', nx, next_month, loc)
            nav_ffM = _mknav(formatter, '&gt;&nbsp;', nx, ff_month, loc)
            nav_nxY = _mknav(formatter, '&gt;&gt;', nx, next_year, loc)

            # Add buttons for going to previous months and year.
            buff(nav_pvY, nav_frM, nav_pvM)

        # The caption will always be there.
        heading = tag.td(format_datetime(today, 'MMMM y', locale=loc))
        buff = buff(heading(class_='y'))

        if showbuttons is True:
            # Add buttons for going to next months and year.
            buff(nav_nxM, nav_ffM, nav_nxY)
        buff = tag.caption(tag.table(tag.tbody(buff)))
        buff = tag.table(buff)
        if name == 'WikiTicketCalendar':
            if cal_width.startswith('+') is True:
                width=":".join(['min-width', cal_width]) 
                buff(class_='wikitcalendar', style=width)
            else:
                buff(class_='wikitcalendar')
        if name == 'WikiCalendar':
                buff(class_='wiki-calendar')

        heading = tag.tr()
        heading(align='center')

        for idx, day_name in get_day_names('abbreviated',
                                           'format', loc).iteritems():
            col = tag.th(day_name)
            col(class_=('workday', 'weekend')[idx > 4], scope='col')
            heading(col)
        heading = buff(tag.thead(heading))

        # Building main calendar table body
        buff = tag.tbody()
        day = first_day_cal - timedelta(1)
        while day < last_day_cal:
            day += timedelta(1)
            # Insert a new row for every first-day-of-week.
            if int(format_datetime(day, 'c', locale=loc)) == 1:
                line = tag.tr()
                line(align='right')
            if not (day < first_day_month or day > last_day_month):
                # check for wikipage with name specified in
                # 'wiki_page_format'
                wiki = format_date(day, wiki_page_format)
                if day == today:
                    a_class = 'day today'
                    td_class = 'today'
                else:
                    a_class = 'day'
                    td_class = 'day'

                if uts:
                    day_ts = to_utimestamp(day)
                    day_ts_eod = day_ts + 86399999999
                else:
                    day_ts = to_timestamp(day)
                    day_ts_eod = day_ts + 86399

                # check for milestone(s) on that day
                db = env.get_db_cnx()
                cursor = db.cursor()
                cursor.execute("""
                    SELECT name
                      FROM milestone
                     WHERE due >= %s and due <= %s
                """, (day_ts, day_ts_eod))
                milestones = tag()
                for row in cursor:
                    if not a_class.endswith('milestone'):
                        a_class += ' milestone'
                    milestone = to_unicode(row[0])
                    url = env.href.milestone(milestone)
                    milestone = '* ' + milestone
                    milestones = tag(milestones,
                                     tag.div(tag.a(milestone, href=url),
                                             class_='milestone'))
                label = tag.span(day.day)
                label(class_='day')
                if len(wiki_subpages) > 0:
                    pages = tag(label, Markup('<br />'))
                    for page in wiki_subpages:
                        label = tag(' ', page[0])
                        page = '/'.join([wiki, page])
                        pages(self._gen_wiki_links(formatter, args, kwargs,
                                                   page, label, 'subpage',
                                                   check))
                else:
                    pages = self._gen_wiki_links(formatter, args, kwargs,
                                                 wiki, label, a_class, check)
                cell = tag.td(pages)
                cell(class_=td_class, valign='top')
                if name == 'WikiCalendar':
                    line(cell)
                else:
                    if milestones:
                        cell(milestones)
                    else:
                        cell(tag.br())

                    match = []
                    match_od = []
                    ticket_heap = tag('')
                    ticket_list = tag.div('')
                    ticket_list(align='left', class_='condense')

                    # get tickets with due date set to day
                    for t in tickets:
                        due = t.get(self.tkt_due_field)
                        if due is None or due in ['', '--']:
                            continue
                        else:
                            if self.tkt_due_format == 'ts':
                                if not isinstance(due, datetime):
                                    continue
                                if uts:
                                    due_ts = to_utimestamp(due)
                                else:
                                    due_ts = to_timestamp(due)
                                if due_ts < day_ts or due_ts > day_ts_eod:
                                    continue
                            else:
                                # Beware: Format might even be unicode str
                                duedate = format_date(day_dt,
                                                      str(self.tkt_due_format))
                                if not due == duedate:
                                    continue

                        id = t.get('id')
                        ticket, short = _gen_ticket_entry(env, formatter, t)
                        ticket_heap(ticket)
                        if not id in match:
                            if len(match) == 0:
                                ticket_list(short)
                            else:
                                ticket_list(', ', short)
                            match.append(id)

                    # optionally get tickets created on day
                    if show_t_open_dates is True:
                        ticket_od_list = tag.div('')
                        ticket_od_list(align='left',
                                       class_='opendate_condense')

                        for t in tickets:
                            if uts:
                                ticket_ts = to_utimestamp(t.get('time'))
                            else:
                                ticket_ts = to_timestamp(t.get('time'))
                            if ticket_ts < day_ts or ticket_ts > day_ts_eod:
                                continue

                            a_class = 'opendate_'
                            id = t.get('id')
                            ticket, short = _gen_ticket_entry(env, formatter,
                                                              t, a_class)
                            ticket_heap(ticket)
                            if not id in match:
                                if len(match_od) == 0:
                                    ticket_od_list(short)
                                else:
                                    ticket_od_list(', ', short)
                                match_od.append(id)

                    matches = len(match) + len(match_od)
                    if list_condense > 0 and matches >= list_condense:
                        if len(match_od) > 0:
                            if len(match) > 0:
                                ticket_list(', ')
                            ticket_list = tag(ticket_list, ticket_od_list)
                        line(cell(ticket_list))
                    else:
                        line(cell(ticket_heap))
            else:
                if name == 'WikiCalendar':
                    wiki = format_date(day, wiki_page_format)
                    a_class = 'day adjacent_month'
                    pages = self._gen_wiki_links(formatter, args, kwargs,
                                                 wiki, day.day, a_class)

                    cell = tag.td(pages)
                    cell(class_='day adjacent_month')
                    line(cell)
                else:
                    cell = tag.td('')
                    cell(class_='day adjacent_month')
                    line(cell)
            if int(format_datetime(day, 'c', locale=loc)) == 7:
                buff(line)

        buff = tag.div(heading(buff))
        if name == 'WikiTicketCalendar':
            if cal_width.startswith('+') is True:
                width=":".join(['width', cal_width]) 
                buff(class_='wikitcalendar', style=width)
            else:
                buff(class_='wikitcalendar')
        if name == 'WikiCalendar':
                buff(class_='wiki-calendar')
        # Add common CSS stylesheet
        if self.internal_css and not formatter.req.args.get('wikicalendar'):
            # Put definitions directly into the output.
            f = open('/'.join([self.htdocs_path, 'wikicalendar.css']), 'Ur')
            css = tag.style(Markup('<!--\n'), '\n'.join(f.readlines()),
                            Markup('-->\n'))(type="text/css")
            f.close()
            # Add hint to prevent multiple inclusions.
            formatter.req.args['wikicalendar'] = True
            return tag(css, buff)
        elif not formatter.req.args.get('wikicalendar'):
            add_stylesheet(formatter.req, 'wikicalendar/wikicalendar.css')
        return buff

    def _do_check(self, test, item):
        """Execute configurable tests per calendar item."""
        # DEVEL: Fail condition not implemented yet, will need additional
        #   configuration too.
        if test in self.checks.keys():
            sql = self.checks[test].get('test')
            if sql:
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                cursor.execute(sql, (item,))
                row = cursor.fetchone()
                if row is not None:
                    return 1

    def _gen_wiki_links(self, formatter, args, kwargs, wiki, label, a_class,
                        check=None):
        check_sign = None
        url = self.env.href.wiki(wiki)
        if WikiSystem(self.env).has_page(wiki.lstrip('/')):
            a_class += " page"
            title = _("Go to page %s") % wiki
            if check and check[0] == 'link':
                chrome_path = '/'.join([formatter.req.base_path, 'chrome'])
                ok_img = 'wikicalendar/check_ok.png'
                ok = tag.image(src='/'.join([chrome_path, ok_img]),
                               alt='ok', title='ok')
                nok_img = 'wikicalendar/check_nok.png'
                nok = tag.image(src='/'.join([chrome_path, nok_img]),
                                alt='X', title='X')
                unk_img = 'wikicalendar/check_unknown.png'
                unk = tag.image(src='/'.join([chrome_path, unk_img]),
                                alt='?', title='?')
                result = self._do_check(check[1], wiki)
                check_sign = result and (result == 1 and ok or nok) or unk
        else:
            # The default (empty page) is used, if template name is invalid.
            url += "?action=edit"
            # Add page template to create new wiki pages, if specified.
            template = None
            if len(args) >= 6 or kwargs.has_key('base'):
                try:
                    template = kwargs['base']
                except KeyError:
                    template = args[5]
            if template:
                url += "&template=" + template
            title = _("Create page %s") % wiki
        link = tag.a(tag(label), href=url)
        link(class_=a_class, title_=title)
        return tag(link, check_sign)


def _gen_ticket_entry(env, formatter, t, a_class=''):
    id = str(t.get('id'))
    status = t.get('status')
    summary = to_unicode(t.get('summary'))
    owner = to_unicode(t.get('owner'))
    description = to_unicode(t.get('description'))
    url = t.get('href')

    if status == 'closed':
        a_class = a_class + 'closed'
    else:
        a_class = a_class + 'open'

    # Reduce content for tooltips.
    markup = format_to_html(env, formatter.context, description)
    extractor = TextExtractor()
    extractor.feed(markup)
    tip = tag.span(shorten_line(extractor.getvalue()))

    ticket = '#' + id
    ticket = tag.a(ticket, href=url)
    ticket(tip, class_='tip', target='_blank')
    ticket = tag.div(ticket)
    ticket(class_=a_class, align='left')
    # fix stripping of regular leading space in IE
    blank = '&nbsp;'
    ticket(Markup(blank), summary, ' (', owner, ')')

    summary = tag(summary, ' (', owner, ')')
    ticket_short = '#' + id
    ticket_short = tag.a(ticket_short, href=url)
    ticket_short(target='_blank', title_=summary)
    ticket_short = tag.span(ticket_short)
    ticket_short(class_=a_class)

    return ticket, ticket_short

def _mknav(formatter, label, a_class, dt, locale):
    """The calendar nav button builder.

    This is a convenience module for shorter and better serviceable code.
    """
    tip = format_datetime(dt, 'MMMM y', locale=locale)
    # URL to the current page
    thispageURL = Href(formatter.req.base_path + formatter.req.path_info)
    url = thispageURL(month=dt.month, year=dt.year)
    markup = tag.a(Markup(label), href=url)
    markup(class_=a_class, title=tip)
    markup = tag.td(markup)
    return markup(class_='x')

def _resolve_relative_name(pagename, referrer):
    """Resolver for Trac wiki page paths.

    This method handles absolute as well as relative wiki paths.
    """
    # Code taken from trac.wiki.api.WikiSystem at r10905,
    # improved by Jun Omae for compatibility with Python2.4.
    if not any(pagename.startswith(prefix) for prefix in ('./', '../')):
        return pagename.lstrip('/')
    base = referrer.split('/')
    components = pagename.split('/')
    for i, comp in enumerate(components):
        if comp == '..':
            if base:
                base.pop()
        elif comp and comp != '.':
            base.extend(components[i:])
            break
    return '/'.join(base)
