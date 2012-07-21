# -*- coding: utf-8 -*-
# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# Copyright (C) 2005 Jan Finell <finell@cenix-bioscience.com>
# Copyright (C) 2007 Mike Comb <mcomb@mac.com>
# Copyright (C) 2008 JaeWook Choi <http://trac-hacks.org/wiki/butterflow>
# Copyright (C) 2008, 2009 W. Martin Borgert <debacle@debian.org>
# Copyright (C) 2010-2012 Steffen Hoffmann <hoff.st@shaas.net>
#
# "THE BEER-WARE LICENSE" (Revision 42):
# <trac@matt-good.net> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff.  If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.  Matthew Good
# (Beer-ware license written by Poul-Henning Kamp
#  http://people.freebsd.org/~phk/)
#
# Author: Matthew Good <trac@matt-good.net>
# See changelog for a detailed history

import calendar
import datetime
import locale
import re
import sys

from genshi.builder         import tag
from genshi.core            import escape, Markup
from pkg_resources          import resource_filename
from sgmllib                import SGMLParser

from trac.config            import BoolOption, Configuration, Option
from trac.core              import Component, implements
from trac.util.datefmt      import format_date
from trac.util.text         import shorten_line, to_unicode
from trac.web.href          import Href
from trac.web.chrome        import add_stylesheet, ITemplateProvider
from trac.wiki.api          import parse_args, IWikiMacroProvider, \
                                   WikiSystem
from trac.wiki.formatter    import format_to_html

from wikicalendar.api       import add_domain, _, tag_
from wikicalendar.ticket    import WikiCalendarTicketProvider

uts = None
try:
    from trac.util.datefmt  import to_utimestamp
    uts = "env with POSIX microsecond time stamps found"
except ImportError:
    # fallback to old module for 0.11 compatibility
    from trac.util.datefmt  import to_timestamp


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
    """Provides macros to display wiki page navigation in a calendar view.
    """

    implements(IWikiMacroProvider, ITemplateProvider)

    # generic [wikicalendar] section
    internal_css = BoolOption('wikicalendar', 'internal_css', False,
                              """Whether CSS should be embedded into the
                              HTML. This is meant as fallback, if linking
                              the external style sheet file fails.""")

    #  [wikiticketcalendar] section
    due_field_name = Option('wikiticketcalendar', 'ticket.due_field.name',
                            'due_close', doc = """Custom due date field name
                            to evaluate for displaying tickets by date.""")
    due_field_fmt = Option('wikiticketcalendar', 'ticket.due_field.format',
                           '%y-%m-%d', doc = """Custom due date value format,
                           that is any expression supported by strftime or
                           'ts' identifier for POSIX microsecond time stamps
                           as supported in later Trac versions.""")

    htdocs_path = resource_filename(__name__, 'htdocs')

    def __init__(self):
        # bind 'wikicalendar' catalog to the specified locale directory
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

        # Read options from Trac configuration system, adjustable in trac.ini.
        #  [wiki] section
        self.sanitize = True
        if self.config.getbool('wiki', 'render_unsafe_content') is True:
            self.sanitize = False

        # TRANSLATOR: Keep macro doc style formatting here, please.
        self.doc_calendar = _(
    """Inserts a small calendar where each day links to a wiki page whose name
    matches `wiki-page-format`. The current day is highlighted, and days with
    Milestones are marked in bold. This version makes heavy use of CSS for
    formatting.
    
    Usage:
    {{{
    [[WikiCalendar([year, [month, [show-buttons, [wiki-page-format]]]])]]
    }}}
    
    Arguments:
     1. `year` (4-digit year) - defaults to `*` (current year)
     1. `month` (2-digit month) - defaults to `*` (current month)
     1. `show-buttons` (boolean) - defaults to `true`
     1. `wiki-page-format` (string) - defaults to `%Y-%m-%d`
    
    Examples:
    {{{
    [[WikiCalendar(2006,07)]]
    [[WikiCalendar(2006,07,false)]]
    [[WikiCalendar(*,*,true,Meeting-%Y-%m-%d)]]
    [[WikiCalendar(2006,07,false,Meeting-%Y-%m-%d)]]
    }}}
    """)
        self.doc_ticketcalendar = _(
    """Display Milestones and Tickets in a calendar view.

    displays a calendar, the days link to:
     - milestones (day in bold) if there is one on that day
     - a wiki page that has wiki_page_format (if exist)
     - create that wiki page if it does not exist
     - use page template (if exist) for new wiki page
    """)

    # ITemplateProvider methods
    # Returns additional path where stylesheets are placed.
    def get_htdocs_dirs(self):
        return [('wikicalendar', self.htdocs_path)]

    # Returns additional path where templates are placed.
    def get_templates_dirs(self):
        return []

    # IWikiMacroProvider methods
    # Returns list of provided macro names.
    def get_macros(self):
        yield "WikiCalendar"
        yield "WikiTicketCalendar"

    # Returns documentation for provided macros.
    def get_macro_description(self, name):
        if name == 'WikiCalendar':
            return self.doc_calendar
        if name == 'WikiTicketCalendar':
            return self.doc_ticketcalendar

    def _mkdatetime(self, year, month, day=1):
        """A custom 'datetime' object builder.

        This is a convenience module for shortening function calls.
        It uses Trac's timezone setting.
        """
        dt = datetime.datetime(year, month, day, tzinfo=self.tz_info)
        return dt

    def _mknav(self, label, a_class, month, year):
        """The calendar nav button builder.

        This is a convenience module for shorter and better serviceable code.
        """
        tip = to_unicode(format_date(self._mkdatetime(year, month), '%B %Y'))
        # URL to the current page
        thispageURL = Href(self.ref.req.base_path + self.ref.req.path_info)
        url = thispageURL(month=month, year=year)
        markup = tag.a(Markup(label), href=url)
        markup(class_=a_class, title=tip)
        markup = tag.td(markup)
        return markup(class_='x')

    def _gen_wiki_links(self, wiki, label, a_class, url, wiki_page_template,
                        check=None):
        check_sign = None
        if WikiSystem(self.env).has_page(wiki.lstrip('/')):
            a_class += " page"
            title = _("Go to page %s") % wiki
            if check and check[0] == 'link':
                chrome_path = '/'.join([self.ref.req.base_path, 'chrome'])
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
            url += "?action=edit"
            # adding template name, if specified
            if wiki_page_template != "":
                url += "&template=" + wiki_page_template
            title = _("Create page %s") % wiki
        link = tag.a(tag(label), href=url)
        link(class_=a_class, title_=title)
        return tag(link, check_sign)

    def _gen_ticket_entry(self, t, a_class=''):
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
        markup = format_to_html(self.env, self.ref.context, description)
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

        return ticket,ticket_short

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

    def _resolve_relative_name(self, pagename, referrer):
        """Resolver for Trac wiki page paths.

        This method handles absolute as well as relative wiki paths.
        """
        # Code taken from trac.wiki.api.WikiSystem at r10905.
        if not pagename.startswith(('./', '../')):
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

    # Returns macro content.
    def expand_macro(self, formatter, name, arguments):

        self.ref = formatter
        self.tz_info = formatter.req.tz
        self.thistime = datetime.datetime.now(self.tz_info)

        # Parse arguments from macro invocation
        args, kwargs = parse_args(arguments, strict=False)

        # Find out whether use http param, current or macro param year/month
        http_param_year = formatter.req.args.get('year','')
        http_param_month = formatter.req.args.get('month','')

        if http_param_year == "":
            # not clicked on a prev or next button
            if len(args) >= 1 and args[0] <> "*":
                # year given in macro parameters
                year = int(args[0])
            else:
                # use current year
                year = self.thistime.year
        else:
            # year in http params (clicked by user) overrides everything
            year = int(http_param_year)

        if http_param_month == "":
            # not clicked on a prev or next button
            if len(args) >= 2 and args[1] <> "*":
                # month given in macro parameters
                month = int(args[1])
            else:
                # use current month
                month = self.thistime.month
        else:
            # month in http params (clicked by user) overrides everything
            month = int(http_param_month)

        showbuttons = True
        if len(args) >= 3 or kwargs.has_key('nav'):
            try:
                showbuttons = kwargs['nav'] in ["True", "true", "yes", "1"]
            except KeyError:
                showbuttons = args[2] in ["True", "true", "yes", "1"]

        wiki_page_format = "%Y-%m-%d"
        if len(args) >= 4 and args[3] != "*" or kwargs.has_key('wiki'):
            try:
                wiki_page_format = str(kwargs['wiki'])
            except KeyError:
                wiki_page_format = str(args[3])
        # Support relative paths in macro arguments for wiki page links.
        wiki_page_format = self._resolve_relative_name(wiki_page_format,
                                                       formatter.resource.id)

        list_condense = 0
        show_t_open_dates = True
        wiki_page_template = ""
        wiki_subpages = []

        # Read optional check plan.
        check = []
        if kwargs.has_key('check'):
            check = kwargs['check'].split('.')

        if name == 'WikiTicketCalendar':
            if len(args) >= 5 or kwargs.has_key('cdate'):
                try:
                    show_t_open_dates = kwargs['cdate'] in \
                                               ["True", "true", "yes", "1"]
                except KeyError:
                    show_t_open_dates = args[4] in \
                                               ["True", "true", "yes", "1"]

            # template name tried to create new pages
            # optional, default (empty page) is used, if name is invalid
            if len(args) >= 6 or kwargs.has_key('base'):
                try:
                    wiki_page_template = kwargs['base']
                except KeyError:
                    wiki_page_template = args[5]

            # TracQuery support for ticket selection
            query_args = "id!=0"
            if len(args) >= 7 or kwargs.has_key('query'):
                # prefer query arguments provided by kwargs
                try:
                    query_args = kwargs['query']
                except KeyError:
                    query_args = args[6]
            tickets = WikiCalendarTicketProvider(self.env)
            self.tickets = tickets.harvest(formatter.req, query_args)

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

            # Can use this to change the day the week starts on,
            # but this is a system-wide setting.
            calendar.setfirstweekday(calendar.MONDAY)

        cal = calendar.monthcalendar(year, month)
        curr_day = None
        if year == self.thistime.year and month == self.thistime.month:
            curr_day = self.thistime.day

        # for prev/next navigation links
        prevMonth = month - 1
        nextMonth = month + 1
        nextYear = prevYear = year
        # check for year change (KISS version)
        if prevMonth == 0:
            prevMonth = 12
            prevYear -= 1
        if nextMonth == 13:
            nextMonth = 1
            nextYear += 1

        # for fast-forward/-rewind navigation links
        ffYear = frYear = year
        if month < 4:
            frMonth = month + 9
            frYear -= 1
        else:
            frMonth = month - 3
        if month > 9:
            ffMonth = month - 9
            ffYear += 1
        else:
            ffMonth = month + 3

        last_week_prevMonth = calendar.monthcalendar(prevYear, prevMonth)[-1]
        first_week_nextMonth = calendar.monthcalendar(nextYear, nextMonth)[0]

        # Switch to user's locale, if available.
        try:
            loc_req = str(formatter.req.locale)
        except AttributeError:
            # Available since in Trac 0.12 .
            loc_req = None
        if loc_req:
            loc = locale.getlocale()
            loc_prop = locale.normalize(loc_req)
            try:
                locale.setlocale(locale.LC_TIME, loc_prop)
            except locale.Error:
                try:
                    # Re-try with UTF-8 as last resort.
                    loc_prop = '.'.join([loc_prop.split('.')[0],'utf8'])
                    locale.setlocale(locale.LC_TIME, loc_prop)
                except locale.Error:
                    loc_prop = None
            self.env.log.debug('Locale setting for calendar: ' + str(loc_prop))

        # Finally building the output
        # Begin with caption and optional navigation links
        buff = tag.tr()

        if showbuttons is True:
            # calendar navigation buttons
            nx = 'next'
            pv = 'prev'
            nav_pvY = self._mknav('&lt;&lt;', pv, month, year-1)
            nav_frM = self._mknav('&nbsp;&lt;', pv, frMonth, frYear)
            nav_pvM = self._mknav('&nbsp;&laquo;', pv, prevMonth, prevYear)
            nav_nxM = self._mknav('&raquo;&nbsp;', nx, nextMonth, nextYear)
            nav_ffM = self._mknav('&gt;&nbsp;', nx, ffMonth, ffYear)
            nav_nxY = self._mknav('&gt;&gt;', nx, month, year+1)

            # add buttons for going to previous months and year
            buff(nav_pvY, nav_frM, nav_pvM)

        # The caption will always be there.
        heading = tag.td(
             to_unicode(format_date(self._mkdatetime(year, month), '%B %Y')))
        buff = buff(heading(class_='y'))

        if showbuttons is True:
            # add buttons for going to next months and year
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

        for day in calendar.weekheader(2).split()[:-2]:
            col = tag.th(to_unicode(day))
            col(class_='workday', scope='col')
            heading(col)
        for day in calendar.weekheader(2).split()[-2:]:
            col = tag.th(to_unicode(day))
            col(class_='weekend', scope='col')
            heading(col)

        heading = buff(tag.thead(heading))

        # Building main calendar table body
        buff = tag.tbody()
        w = -1
        for week in cal:
            w = w + 1
            line = tag.tr()
            line(align='right')
            d = -1
            for day in week:
                d = d + 1
                if day:
                    # check for wikipage with name specified in
                    # 'wiki_page_format'
                    wiki = format_date(self._mkdatetime(year, month, day),
                                                         wiki_page_format)
                    if day == curr_day:
                        a_class = 'day today'
                        td_class = 'today'
                    else:
                        a_class = 'day'
                        td_class = 'day'

                    day_dt = self._mkdatetime(year, month, day)
                    if uts:
                        day_ts = to_utimestamp(day_dt)
                        day_ts_eod = day_ts + 86399999999
                    else:
                        day_ts = to_timestamp(day_dt)
                        day_ts_eod = day_ts + 86399

                    # check for milestone(s) on that day
                    db = self.env.get_db_cnx()
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
                        url = self.env.href.milestone(milestone)
                        milestone = '* ' + milestone
                        milestones = tag(milestones,
                                         tag.div(tag.a(milestone, href=url),
                                                 class_='milestone'))
                    day = tag.span(day)
                    day(class_='day')
                    if len(wiki_subpages) > 0:
                        pages = tag(day, Markup('<br />'))
                        for page in wiki_subpages:
                            label = tag(' ', page[0])
                            page = '/'.join([wiki, page])
                            url = self.env.href.wiki(page)
                            pages(self._gen_wiki_links(page, label, 'subpage',
                                                     url, wiki_page_template,
                                                     check))
                    else:
                        url = self.env.href.wiki(wiki)
                        pages = self._gen_wiki_links(wiki, day, a_class,
                                                     url, wiki_page_template,
                                                     check)
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
                        for t in self.tickets:
                            due = t.get(self.due_field_name)
                            if due is None or due in ['', '--']:
                                continue
                            else:
                                if self.due_field_fmt == 'ts':
                                    if not isinstance(due, datetime.datetime):
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
                                                      str(self.due_field_fmt))
                                    if not due == duedate:
                                        continue

                            id = t.get('id')
                            ticket, short = self._gen_ticket_entry(t)
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

                            for t in self.tickets:
                                if uts:
                                    ticket_ts = to_utimestamp(t.get('time'))
                                else:
                                    ticket_ts = to_timestamp(t.get('time'))
                                if ticket_ts < day_ts or \
                                        ticket_ts > day_ts_eod:
                                    continue

                                a_class = 'opendate_'
                                id = t.get('id')
                                ticket, short = self._gen_ticket_entry(t,
                                                                  a_class)
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
                        if w == 0:
                            day = last_week_prevMonth[d]
                            wiki = format_date(self._mkdatetime(
                                prevYear, prevMonth, day), wiki_page_format)
                        else:
                            day = first_week_nextMonth[d]
                            wiki = format_date(self._mkdatetime(
                                nextYear, nextMonth, day), wiki_page_format)
                        url = self.env.href.wiki(wiki)
                        a_class = 'day adjacent_month'
                        pages = self._gen_wiki_links(wiki, day, a_class,
                                                 url, wiki_page_template)

                        cell = tag.td(pages)
                        cell(class_='day adjacent_month')
                        line(cell)
                    else:
                        cell = tag.td('')
                        cell(class_='day adjacent_month')
                        line(cell)
            buff(line)

        if loc_req and loc_prop:
            # We may have switched to users locale, resetting now.
            try:
                locale.setlocale(locale.LC_ALL, loc)
                self.env.log.debug('Locale setting restored: ' + str(loc))
            except locale.Error:
                pass

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
        if self.internal_css and not self.ref.req.args.get('wikicalendar'):
            # Put definitions directly into the output.
            f = open('/'.join([self.htdocs_path, 'wikicalendar.css']), 'Ur')
            css = tag.style(Markup('<!--\n'), '\n'.join(f.readlines()),
                            Markup('-->\n'))(type="text/css")
            f.close()
            # Add hint to prevent multiple inclusions.
            self.ref.req.args['wikicalendar'] = True
            return tag(css, buff)
        elif not self.ref.req.args.get('wikicalendar'):
            add_stylesheet(self.ref.req, 'wikicalendar/wikicalendar.css')
        return buff
