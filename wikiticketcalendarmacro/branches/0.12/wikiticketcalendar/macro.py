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
import datetime
import re
import sys

from inspect                import getdoc
from pkg_resources          import resource_filename
from StringIO               import StringIO

from genshi.builder         import tag
from genshi.core            import escape, Markup
from genshi.filters.html    import HTMLSanitizer
from genshi.input           import HTMLParser, ParseError

from trac.config            import Configuration
from trac.core              import implements
from trac.ticket.query      import Query
from trac.util.datefmt      import format_date, to_utimestamp
from trac.util.text         import to_unicode
from trac.util.translation  import domain_functions
from trac.web.href          import Href
from trac.web.chrome        import add_stylesheet, ITemplateProvider
from trac.wiki.api          import parse_args, IWikiMacroProvider, \
                                   WikiSystem
from trac.wiki.formatter    import format_to_html
from trac.wiki.macros       import WikiMacroBase

_, tag_, N_, add_domain = \
    domain_functions('wikiticketcalendar', '_', 'tag_', 'N_', 'add_domain')


__all__ = ['WikiTicketCalendarMacro', ]


class WikiTicketCalendarMacro(WikiMacroBase):
    """Display Milestones and Tickets in a calendar view.

    displays a calendar, the days link to:
     - milestones (day in bold) if there is one on that day
     - a wiki page that has wiki_page_format (if exist)
     - create that wiki page if it does not exist
     - use page template (if exist) for new wiki page
    """

    implements(IWikiMacroProvider, ITemplateProvider)

    def __init__(self):
        # bind the 'foo' catalog to the specified locale directory
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

        # Read options from Trac configuration system, adjustable in trac.ini.
        #  [wiki] section
        self.sanitize = True
        if self.config.getbool('wiki', 'render_unsafe_content') is True:
            self.sanitize = False

        #  [wikiticketcalendar] section
        self.due_field_name = self.config.get('wikiticketcalendar',
                                  'ticket.due_field.name') or 'due_close'
        self.due_field_fmt = self.config.get('wikiticketcalendar',
                                  'ticket.due_field.format') or '%y-%m-%d'

    # ITemplateProvider methods
    # Returns additional path where stylesheets are placed.
    def get_htdocs_dirs(self):
        return [('wikiticketcalendar', resource_filename(__name__, 'htdocs'))]

    # Returns additional path where templates are placed.
    def get_templates_dirs(self):
        return []

    # IWikiMacroProvider methods
    # Returns list of provided macro names.
    def get_macros(self):
        yield "WikiTicketCalendar"

    # Returns documentation for provided macros.
    def get_macro_description(self, name):
        return getdoc(self.__class__)

    # Ticket Query provider
    def _ticket_query(self, formatter, content):
        """
        A custom TicketQuery macro implementation.

        Most lines were taken directly from that code.
        *** Original Comments as follows (shortend)***
        Macro that lists tickets that match certain criteria.

        This macro accepts a comma-separated list of keyed parameters,
        in the form "key=value".

        If the key is the name of a field, the value must use the syntax
        of a filter specifier as defined in TracQuery#QueryLanguage.
        Note that this is ''not'' the same as the simplified URL syntax
        used for `query:` links starting with a `?` character.

        In addition to filters, several other named parameters can be used
        to control how the results are presented. All of them are optional.

        Also, using "&" as a field separator still works but is deprecated.
        """
        # Parse args and kwargs.
        argv, kwargs = parse_args(content, strict=False)

        # Define minimal set of values.
        std_fields = ['description', 'owner', 'status', 'summary']
        kwargs['col'] = "|".join(std_fields + [self.due_field_name])

        # Construct the querystring.
        query_string = '&'.join(['%s=%s' %
            item for item in kwargs.iteritems()])

        # Get the Query Object.
        query = Query.from_string(self.env, query_string)

        # Get the tickets.
        tickets = self._get_tickets(query, formatter.req)
        return tickets

    def _get_tickets(self, query, req):
        '''Returns a list of ticket objects.'''
        rawtickets = query.execute(req) # Get all tickets
        # Do permissions check on tickets
        tickets = [t for t in rawtickets
                   if 'TICKET_VIEW' in req.perm('ticket', t['id'])]
        return tickets

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

        return markup

    def _gen_ticket_entry(self, t, a_class=''):
        id = str(t.get('id'))
        status = t.get('status')
        summary = to_unicode(t.get('summary'))
        owner = to_unicode(t.get('owner'))
        description = to_unicode(t.get('description')[:1024])
        url = t.get('href')

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

        summary = tag(summary, ' (', owner, ')')
        ticket_short = '#' + id
        ticket_short = tag.a(ticket_short, href=url)
        ticket_short(target='_blank', title_=summary)
        ticket_short = tag.span(ticket_short)
        ticket_short(class_=a_class)

        return ticket,ticket_short

    # Returns macro content.
    def expand_macro(self, formatter, name, arguments):

        self.ref = formatter
        self.tz_info = formatter.req.tz
        self.thistime = datetime.datetime.now(self.tz_info)

        # Add CSS stylesheet
        add_stylesheet(self.ref.req,
            'wikiticketcalendar/css/wikiticketcalendar.css')


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

        show_t_open_dates = True
        if len(args) >= 5 or kwargs.has_key('cdate'):
            try:
                show_t_open_dates = kwargs['cdate'] in \
                                               ["True", "true", "yes", "1"]
            except KeyError:
                show_t_open_dates = args[4] in ["True", "true", "yes", "1"]

        # template name tried to create new pages
        # optional, default (empty page) is used, if name is invalid
        wiki_page_template = ""
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
        self.tickets = self._ticket_query(formatter, query_args)

        # compress long ticket lists
        list_condense = 0
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


        # Can use this to change the day the week starts on,
        # but this is a system-wide setting.
        calendar.setfirstweekday(calendar.MONDAY)
        cal = calendar.monthcalendar(year, month)

        curr_day = None
        if year == self.thistime.year and month == self.thistime.month:
            curr_day = self.thistime.day

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
        # Begin with caption and optional navigation links
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
        buff(tag.strong(to_unicode(format_date(self._mkdatetime(
                                               year, month), '%B %Y'))))

        if showbuttons is True:
            # add buttons for going to next months and year
            buff(nav_nxM, nav_ffM, nav_nxY)

        buff = tag.table(buff)
        width=":".join(['min-width', cal_width]) 
        buff(class_='wikiTicketCalendar', style=width)

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
                    line(cell)
                else:
                    # check for wikipage with name specified in
                    # 'wiki_page_format'
                    wiki = format_date(self._mkdatetime(year, month, day),
                                                         wiki_page_format)
                    url = self.env.href.wiki(wiki)
                    if WikiSystem(self.env).has_page(wiki):
                        a_class = "day_haspage"
                        title = _("Go to page %s") % wiki
                    else:
                        a_class = "day"
                        url += "?action=edit"
                        # adding template name, if specified
                        if wiki_page_template != "":
                            url += "&template=" + wiki_page_template
                        title = _("Create page %s") % wiki
                    if day == curr_day:
                        td_class = 'today'
                    else:
                        td_class = 'day'

                    cell = tag.a(tag.b(day), href=url)
                    cell(class_=a_class, title_=title)
                    cell = tag.td(cell)
                    cell(class_=td_class, valign='top')

                    day_dt = self._mkdatetime(year, month, day)
                    day_ts = to_utimestamp(day_dt)
                    day_ts_eod = day_ts + 86399999999

                    # check for milestone(s) on that day
                    db = self.env.get_db_cnx()
                    cursor = db.cursor()
                    cursor.execute("""
                        SELECT name
                          FROM milestone
                         WHERE due >= %s and due <= %s
                    """, (day_ts, day_ts_eod))
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
                                due_ts = to_utimestamp(due)
                                if due_ts < day_ts or \
                                    due_ts > day_ts_eod:
                                    continue
                            else:
                                duedate = format_date(day_dt,
                                                      self.due_field_fmt)
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
                            ticket_ts = to_utimestamp(t.get('time'))
                            if ticket_ts < day_ts or ticket_ts > day_ts_eod:
                                continue

                            a_class = 'opendate_'
                            id = t.get('id')
                            ticket, short = self._gen_ticket_entry(t, a_class)
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

            buff(line)

        buff = tag.div(heading(buff))
        if cal_width.startswith('+') is True:
            width=":".join(['width', cal_width]) 
            buff(class_='wikiTicketCalendar', style=width)
        else:
            buff(class_='wikiTicketCalendar')

        return buff
