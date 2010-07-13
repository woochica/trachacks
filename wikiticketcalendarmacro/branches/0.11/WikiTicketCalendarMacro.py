# -*- coding: utf-8 -*-
# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# Copyright (C) 2005 Jan Finell <finell@cenix-bioscience.com>
# Copyright (C) 2007 Mike Comb <mcomb@mac.com>
# Copyright (C) 2008 JaeWook Choi <http://trac-hacks.org/wiki/butterflow>
# Copyright (C) 2008, 2009 W. Martin Borgert <debacle@debian.org>
# Copyright (C) 2010 Steffen Hoffmann <hoff.st@shaas.net>
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
import re
import sys
import time

from datetime               import datetime
from string                 import replace
from StringIO               import StringIO

from genshi.builder         import tag
from genshi.core            import escape, Markup
from genshi.filters.html    import HTMLSanitizer
from genshi.input           import HTMLParser, ParseError

from trac.config            import Configuration
from trac.util.datefmt      import FixedOffset # another import is deferred
from trac.util.text         import to_unicode
from trac.web.href          import Href
from trac.wiki.formatter    import format_to_html
from trac.wiki.api          import WikiSystem
from trac.wiki.macros       import WikiMacroBase

uts = None
try:
    from trac.util.datefmt  import to_utimestamp
    uts = "env with POSIX microsecond time stamps found"
except ImportError:
    # fallback to old module for 0.11 compatibility
    from trac.util.datefmt  import to_timestamp

revision = "$Rev$"
version = "0.8.4"
url = "$URL$"


__all__ = ['WikiTicketCalendarMacro', ]


class WikiTicketCalendarMacro(WikiMacroBase):
    """Display Milestones and Tickets in a calendar view.

    displays a calendar, the days link to:
     - milestones (day in bold) if there is one on that day
     - a wiki page that has wiki_page_format (if exist)
     - create that wiki page if it does not exist
     - use page template (if exist) for new wiki page

    Activate it in 'trac.ini':
    --------
    [components]
    WikiTicketCalendarMacro.* = enabled

    Usage
    -----
    WikiTicketCalendar([year,month,[showbuttons,[wiki_page_format,
        [show_ticket_open_dates,[wiki_page_template]]]]])

    Arguments
    ---------
    year, month = display calendar for month in year
                  ('*' for current year/month)
    showbuttons = true/false, show prev/next buttons
    wiki_page_format = strftime format for wiki pages to display as link
                       (if there is not a milestone placed on that day)
                       (if exist, otherwise link to create page)
                       default is "%Y-%m-%d", '*' for default
    show_ticket_open_dates = true/false, show also when a ticket was opened
    wiki_page_template = wiki template tried to create new page

    Examples
    --------
    WikiTicketCalendar(2006,07)
    WikiTicketCalendar(2006,07,false)
    WikiTicketCalendar(*,*,true,Meeting-%Y-%m-%d)
    WikiTicketCalendar(2006,07,false,Meeting-%Y-%m-%d)
    WikiTicketCalendar(2006,07,true,*,true)
    WikiTicketCalendar(2006,07,true,Meeting-%Y-%m-%d,true,Meeting)
    """

    def __init__(self):
        # Read options from trac.ini's [datafield] section, if existing
        # The format to use for dates. Valid values are dmy, mdy, and ymd.
        self.date_format = self.config.get('datefield', 'format') or 'ymd'
        # The separator character to use for dates.
        self.date_sep = self.config.get('datefield', 'separator') or '-'

        self.sanitize = True
        if self.config.getbool('wiki', 'render_unsafe_content') is True:
            self.sanitize = False

    def _mknav(self, label, a_class, month, year):
        """The calendar nav button builder.

        This is a convenience module for shorter and better serviceable code.
        """
        self.date[0:2] = [year, month]
        tip = to_unicode(time.strftime('%B %Y', tuple(self.date)))
        # URL to the current page
        thispageURL = Href(self.ref.req.base_path + self.ref.req.path_info)
        url = thispageURL(month=month, year=year)
        markup = tag.a(Markup(label), href=url)
        markup(class_=a_class, title=tip)

        return markup

    def _gen_ticket_entry(self, row, a_class=''):
        id = str(row[0])
        url = self.env.href.ticket(id)
        summary = to_unicode(row[1][0:100])
        owner = to_unicode(row[2])
        status = row[3]
        description = to_unicode(row[4][:1024])

        if status == 'closed':
            a_class = a_class + 'closed'
        else:
            a_class = a_class + 'open'
        markup = format_to_html(self.env, self.ref.context, description)
        # Escape, if requested
        if self.sanitize is True:
            try:
                description = HTMLParser(StringIO(markup)
                                           ).parse() | HTMLSanitizer()
            except ParseError:
                description = escape(markup)
        else:
            description = markup

        # Replace tags that destruct tooltips too much
        desc = self.end_RE.sub(']', Markup(description))
        desc = self.del_RE.sub('', desc)
        # need 2nd run after purging newline in table cells in 1st run
        desc = self.del_RE.sub('', desc)
        desc = self.item_RE.sub('X', desc)
        desc = self.tab_RE.sub('[|||]', desc)
        description = self.open_RE.sub('[', desc)

        tip = tag.span(Markup(description))
        ticket = '#' + id
        ticket = tag.a(ticket, href=url)
        ticket(tip, class_='tip', target='_blank')
        ticket = tag.div(ticket)
        ticket(class_=a_class, align='left')
        # fix stripping of regular leading space in IE
        blank = '&nbsp;'
        ticket(Markup(blank), summary, ' (', owner, ')')

        return ticket

    # Returns macro content.
    def expand_macro(self, formatter, name, arguments):

        self.ref = formatter

        # Parse arguments from macro invocation
        if arguments == "":
            args = []
        else:
            args = arguments.split(',')

        # Find out whether use http param, current or macro param year/month
        http_param_year = formatter.req.args.get('year','')
        http_param_month = formatter.req.args.get('month','')
        today = time.localtime()

        if http_param_year == "":
            # not clicked on a prev or next button
            if len(args) >= 1 and args[0] <> "*":
                # year given in macro parameters
                year = int(args[0])
            else:
                # use current year
                year = today.tm_year
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
                month = today.tm_mon
        else:
            # month in http params (clicked by user) overrides everything
            month = int(http_param_month)

        showbuttons = True
        if len(args) >= 3:
            showbuttons = args[2] in ["True", "true", "yes", "1"]

        wiki_page_format = "%Y-%m-%d"
        if len(args) >= 4 and args[3] != "*":
            wiki_page_format = args[3]

        show_ticket_open_dates = True
        if len(args) >= 5:
            show_ticket_open_dates = args[4] in ["True", "true", "yes", "1"]

        # template name tried to create new pages
        # optional, default (empty page) is used, if name is invalid
        wiki_page_template = ""
        if len(args) >= 6:
            wiki_page_template = args[5]


        # Can use this to change the day the week starts on,
        # but this is a system-wide setting.
        calendar.setfirstweekday(calendar.MONDAY)
        cal = calendar.monthcalendar(year, month)

        curr_day = None
        if year == today.tm_year and month == today.tm_mon:
            curr_day = today.tm_mday

        self.date = [year, month + 1] + [1] * 7

        # Compile regex pattern before use for better performance
        pattern_del  = '(?:<span .*?>)|(?:</span>)'
        pattern_del += '|(?:<p>)|(?:<p .*?>)|(?:</p>)'
        pattern_del += '|(?:</table>)|(?:<td.*?\n)|(?:<tr.*?</tr>)'
        self.end_RE  = re.compile('(?:</a>)')
        self.del_RE  = re.compile(pattern_del)
        self.item_RE = re.compile('(?:<img .*?>)')
        self.open_RE = re.compile('(?:<a .*?>)')
        self.tab_RE  = re.compile('(?:<table .*?>)')


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

        # Finally building the output
        # Prepending inline CSS definitions
        styles = """ \
<!--
.wikiTicketCalendar div, table { width: 100%; }
table.wikiTicketCalendar th { font-weight: bold; }
table.wikiTicketCalendar th.workday { width: 17%; }
table.wikiTicketCalendar th.weekend { width: 7%; }
table.wikiTicketCalendar caption {
    font-size: 120%; white-space: nowrap;
    }
table.wikiTicketCalendar caption a {
    display: inline; margin: 0; border: 0; padding: 0;
    background-color: transparent; color: #b00; text-decoration: none;
    }
table.wikiTicketCalendar caption a.prev { padding-right: 5px; font: bold; }
table.wikiTicketCalendar caption a.next { padding-left: 5px; font: bold; }
table.wikiTicketCalendar caption a:hover { background-color: #eee; }
table.wikiTicketCalendar td.today {
    background: #fbfbfb; border-color: #444444; color: #444;
    border-style: solid; border-width: 1px;
    }
table.wikiTicketCalendar td.day {
    background: #e5e5e5; border-color: #444444; color: #333;
    border-style: solid; border-width: 1px;
    }
table.wikiTicketCalendar td.fill {
    background: #eee; border-color: #ccc;
    border-style: solid; border-width: 1px;
    }
table.wikiTicketCalendar div.milestone {
    font-size: 9px; background: #f7f7f0; border: 1px solid #d7d7d7;
    border-bottom-color: #999; text-align: left;
    }
table.wikiTicketCalendar a.day {
    width: 2em; height: 100%; margin: 0; border: 0px; padding: 0;
    color: #333; text-decoration: none;
    }
table.wikiTicketCalendar a.day_haspage {
    width: 2em; height: 100%; margin: 0; border: 0px; padding: 0;
    color: #b00 !important; text-decoration: none;
    }
table.wikiTicketCalendar a.day:hover {
    border-color: #eee; background-color: #eee; color: #000;
    }
table.wikiTicketCalendar div.open   {
    font-size: 9px; color: #000000;
    }
table.wikiTicketCalendar div.closed {
    font-size: 9px; color: #777777; text-decoration: line-through;
    }
table.wikiTicketCalendar div.opendate_open {
    font-size: 9px; color: #000077;
    }
table.wikiTicketCalendar div.opendate_closed {
    font-size: 9px; color: #000077; text-decoration: line-through;
    }

/* pure CSS style tooltip */
a.tip {
    position: relative; cursor: help;
    }
a.tip span { display: none; }
a.tip:hover span {
    display: block; z-index: 1;
    font-size: 0.75em; text-decoration: none;
    /* big left move because of z-index render bug in IE<8 */
    position: absolute; top: 0.8em; left: 6em;
    border: 1px solid #000; background-color: #fff; padding: 5px;
    }
-->
</style>
"""
        styles = tag.style(styles)
        styles(type='text/css')

        # Build caption and optional navigation links
        buff = tag.caption()

        if showbuttons is True:
            # calendar navigation buttons
            nx = 'next'
            pv = 'prev'
            nav_pvY = self._mknav('&nbsp;&lt;&lt;', pv, month, year-1)
            nav_frM = self._mknav('&nbsp;&lt;&nbsp;', pv, frMonth, frYear)
            nav_pvM = self._mknav('&nbsp;&laquo;&nbsp;', pv, prevMonth,
                                                                 prevYear)
            nav_nxM = self._mknav('&nbsp;&raquo;&nbsp;', nx, nextMonth,
                                                                 nextYear)
            nav_ffM = self._mknav('&nbsp;&gt;&nbsp;', nx, ffMonth, ffYear)
            nav_nxY = self._mknav('&nbsp;&gt;&gt;', nx, month, year+1)

            # add buttons for going to previous months and year
            buff(nav_pvY, nav_frM, nav_pvM)

        # The caption will always be there.
        self.date[0:2] = [year, month]
        buff(tag.strong(to_unicode(time.strftime('%B %Y', tuple(self.date)))))

        if showbuttons is True:
            # add buttons for going to next months and year
            buff(nav_nxM, nav_ffM, nav_nxY)

        buff = tag.table(buff)
        buff(class_='wikiTicketCalendar')

        heading = tag.tr()
        heading(align='center')

        for day in calendar.weekheader(2).split()[:-2]:
            col = tag.th(day)
            col(class_='workday', scope='col')
            heading(col)
        for day in calendar.weekheader(2).split()[-2:]:
            col = tag.th(day)
            col(class_='weekend', scope='col')
            heading(col)

        heading = buff(tag.thead(heading))

        # Building main calendar table body
        buff = tag.tbody()
        for row in cal:
            line = tag.tr()
            line(align='right')
            for day in row:
                if not day:
                    cell = tag.td('')
                    cell(class_='fill')
                else:
                    db = self.env.get_db_cnx()
                    cursor = db.cursor()
                    utc = FixedOffset(0, 'UTC')
                    if uts:
                        duedatestamp = t = to_utimestamp(datetime(year, month,
                                                 day, 0, 0, 0, 0, tzinfo=utc))
                        duedatestamp_eod = t + 86399999999
                    else:
                        duedatestamp = t = to_timestamp(datetime(year, month,
                                                day, 0, 0, 0, 0, tzinfo=utc))
                        duedatestamp_eod = t + 86399

                    dayString = "%02d" % day
                    monthString = "%02d" % month
                    yearString = "%04d" % year

                    # check for wikipage with name specified in
                    # 'wiki_page_format'
                    self.date[0:3] = [year, month, day]
                    if day == curr_day:
                        td_class = 'today'
                    else:
                        td_class = 'day'
                    wiki = time.strftime(wiki_page_format, tuple(self.date))
                    url = self.env.href.wiki(wiki)
                    if WikiSystem(self.env).has_page(wiki):
                        a_class = "day_haspage"
                        title = "Go to page %s" % wiki
                    else:
                        a_class = "day"
                        url += "?action=edit"
                        # adding template name, if specified
                        if wiki_page_template != "":
                            url += "&template=" + wiki_page_template
                        title = "Create page %s" % wiki

                    cell = tag.a(tag.b(day), href=url)
                    cell(class_=a_class, title_=title)
                    cell = tag.td(cell)
                    cell(class_=td_class, valign='top')

                    # Use get to handle default format
                    duedate = { 'dmy': '%(dd)s%(sep)s%(mm)s%(sep)s%(yy)s',
                                'mdy': '%(mm)s%(sep)s%(dd)s%(sep)s%(yy)s',
                                'ymd': '%(yy)s%(sep)s%(mm)s%(sep)s%(dd)s'
                    }.get(self.date_format,
                    '%(yy)s%(sep)s%(mm)s%(sep)s%(dd)s') % {
                        'dd': dayString,
                        'mm': monthString,
                        'yy': yearString,
                        'sep': self.date_sep
                    }

                    # at first check for milestone on that day
                    cursor.execute("""
                        SELECT name
                          FROM milestone
                         WHERE due >= %s and due < %s
                    """, (duedatestamp, duedatestamp_eod))
                    while (1):
                        row = cursor.fetchone()
                        if row is None:
                            cell(tag.br())
                            break
                        else:
                            name = to_unicode(row[0])
                            url = self.env.href.milestone(name)
                            milestone = '* ' + name
                            milestone = tag.div(tag.a(milestone, href=url))
                            milestone(class_='milestone')

                            cell(milestone)

                    # get tickets with due date set to day
                    cursor.execute("""
                        SELECT t.id,t.summary,t.owner,t.status,t.description
                          FROM ticket t, ticket_custom tc
                         WHERE tc.ticket=t.id and tc.name='due_close' and
                               tc.value=%s
                    """, (duedate, ))
                    while (1):
                        row = cursor.fetchone()
                        if row is None:
                            break
                        else:
                            ticket = self._gen_ticket_entry(row)

                            cell(ticket)

                    if show_ticket_open_dates is True:
                        # get tickets created on day
                        cursor.execute("""
                            SELECT t.id,t.summary,t.owner,t.status,
                                   t.description,t.time
                              FROM ticket t
                        """)
                        while (1):
                            row = cursor.fetchone()
                            if row is None:
                                break

                            ticket_time = int(row[5])
                            if ticket_time < duedatestamp or \
                                    ticket_time > duedatestamp_eod:
                                continue

                            a_class = 'opendate_'
                            ticket = self._gen_ticket_entry(row, a_class)

                            cell(ticket)

                line(cell)
            buff(line)

        buff = tag.div(heading(buff))
        buff(class_='wikiTicketCalendar')

        # Finally prepend prepared CSS styles
        buff = tag(styles, buff) 
        
        return buff
