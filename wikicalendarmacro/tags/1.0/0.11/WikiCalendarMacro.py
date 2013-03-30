# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# Copyright (C) 2005 Jan Finell <finell@cenix-bioscience.com> 
#
# "THE BEER-WARE LICENSE" (Revision 42):
# <trac@matt-good.net> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff.  If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.  Matthew Good
# (Beer-ware license written by Poul-Henning Kamp
#  http://people.freebsd.org/~phk/)
#
# Author: Matthew Good <trac@matt-good.net>
# Month/Year navigation by: Jan Finell <finell@cenix-bioscience.com>
# trac 0.11 compatibility by: Vlad Sukhoy <vladimir.sukhoy@gmail.com>
# refactored; CSS added by: Andy Schlaikjer <andrew.schlaikjer@gmail.com>
# python 2.4 fix by: JasonWinnebeck
# more CSS tweaks by: Andy Schlaikjer <andrew.schlaikjer@gmail.com>

import time
import calendar
from cStringIO import StringIO
from trac.resource import get_relative_resource, get_resource_url 
from trac.wiki.api import WikiSystem
from trac.wiki.macros import WikiMacroBase
from trac.web.href import Href
from trac.util import *

revision="$Rev$"
url="$URL$"

class WikiCalendarMacro(WikiMacroBase):
    
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
    """
    
    def expand_macro(self, formatter, name, content):
        today = time.localtime()
        # VS: The hdf is gone in 0.11, using request object instead
        http_param_year = formatter.req.args.get('year', '')
        http_param_month = formatter.req.args.get('month', '')
        if content == "":
            args = []
        else:
            args = content.split(',', 3)
        
        # find out whether use http param, current or macro param year/month
        
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
        
        showbuttons = 1
        if len(args) >= 3:
            showbuttons = bool(args[2]=="True" or args[2]=="true" or args[2]=="no" or args[2]=="0")
        
        wiki_page_format = "%Y-%m-%d"
        if len(args) >= 4:
            wiki_page_format = args[3]
        
        curr_day = None
        if year == today.tm_year and month == today.tm_mon:
            curr_day = today.tm_mday
        
        # url to the current page (used in the navigation links)
        # VS: hdf is gone in 0.11, using the new "Context" object instead
        # AS: trac.web.Href object used instead of basic strings
        # JW: context doesn't seem to have the right href, so we get it from
        #     the req; hopefully should work regardless of Trac base_url
        #     setting or anything like that.
        thispageURL = Href( formatter.req.base_path + formatter.req.path_info )
        #thispageURL = formatter.context.href   # DEM -- original 6.0, but used in 4.1

        # for the prev/next navigation links
        prevMonth = month-1
        prevYear  = year
        nextMonth = month+1
        nextYear  = year
        # check for year change (KISS version)
        if prevMonth == 0:
            prevMonth = 12
            prevYear -= 1
        if nextMonth == 13:
            nextMonth = 1
            nextYear += 1
        
        # 9-tuple for use with time.* functions requiring a struct_time
        # argument. The ninth value of -1 signals "do the right thing"
        # w.r.t. daylight savings time.
        date = [0] * 8 + [-1] # AS: breaks Python 2.4
        # date = list( today ) # AS: breaks SQL query
        
        # building the output
        buff = StringIO()
        buff.write('''\
<style type="text/css">
<!--
table.wiki-calendar { margin: 0; border: none; padding: 0; border-collapse: collapse; }
table.wiki-calendar caption { font-size: 120%; white-space: nowrap; }
table.wiki-calendar caption a { display: inline; margin: 0; border: 0; padding: 0; background-color: transparent; color: #b00; text-decoration: none;}
table.wiki-calendar caption a.prev { padding-right: 12px; font-size:9pt; }
table.wiki-calendar caption a.prevm {padding-right: 0px;font-size:9pt;}
table.wiki-calendar caption a.next { padding-left: 12px;font-size:9pt; }
table.wiki-calendar caption a.nextm {padding-left: 0px;font-size:9pt}
table.wiki-calendar td.x {}
table.wiki-calendar td.y {text-align:center; width:120%;font-size: 10pt;font-weight:bold;}
table.wiki-calendar caption a:hover { background-color: #eee; }
table.wiki-calendar th { border: none; border-bottom: 2px solid #000; text-align: center; font-weight: bold; }
table.wiki-calendar td { padding: 0; border: none; text-align: right; }
table.wiki-calendar a.day { display: block; width: 2em; height: 100%; margin: 0; border: 2px solid #fff; padding: 0; background-color: #fff; color: #888; text-decoration: none; }
table.wiki-calendar a.day:hover { border-color: #eee; background-color: #eee; color: #000; }
table.wiki-calendar a.today { border-color: #b00 !important; }
table.wiki-calendar a.adjacent_month { border-color: #f0f0f0; background-color: #f0f0f0; }
table.wiki-calendar a.milestone { font-weight: bold; }
table.wiki-calendar a.page { color: #b00 !important; }
//-->
</style>
<table class="wiki-calendar"><caption>
''')
        if showbuttons:
            # prev year link
            date[0:2] = [year-1, month]
            buff.write('<table><tr><td class="x"><a class="prev" href="%(url)s" title="%(title)s">&lt;&lt;</a></td>' % {
                'url': thispageURL(month=month, year=year-1),
                'title': time.strftime('%B %Y', tuple(date))
                })
            # prev month link
            date[0:2] = [prevYear, prevMonth]
            buff.write('<td class="x"><a class="prevm" href="%(url)s" title="%(title)s">&lt;</a></td>' % {
                'url': thispageURL(month=prevMonth, year=prevYear),
                'title': time.strftime('%B %Y', tuple(date))
                })
       
        # Look up the first weekday. The general procedure came from
        # http://blogs.gnome.org/patrys/2008/09/29/how-to-determine-the-first-day-of-week/
        def getfirstweekday():
            from os import popen, environ
            import datetime
            from re import search

            locale = popen("locale first_weekday week-1stday", "r")
            output = locale.read().strip().split("\n")

            offs, date = output
            y, m, d = re.search("^(\d{4})(\d{2})(\d{2})$", date).groups()

            firstweekday = datetime.date(int(y), int(m), int(d)) + \
                datetime.timedelta(days = int(offs) - 1)

            return firstweekday.weekday()

        calendar.setfirstweekday(getfirstweekday())
 
        # the caption
        date[0:2] = [year, month]
        if showbuttons:
            buff.write('<td class="y">%(title)s</td>' %{'title': time.strftime('%B %Y', tuple(date))})
        else:
            buff.write(time.strftime('%B %Y', tuple(date)))
        
        if showbuttons:
             # next month link
            date[0:2] = [nextYear, nextMonth]
            buff.write('<td class="x"><a class="nextm" href="%(url)s" title="%(title)s">&gt;</a></td>' % {
                'url': thispageURL(month=nextMonth, year=nextYear),
                'title': time.strftime('%B %Y', tuple(date))
                })
            # next year link
            date[0:2] = [year+1, month]
            buff.write('<td class="x"><a class="next" href="%(url)s" title="%(title)s">&gt;&gt;</a></td></tr></table>' % {
                'url': thispageURL(month=month, year=year+1),
                'title': time.strftime('%B %Y', tuple(date))
                })
            
        buff.write('</caption>\n<thead>\n<tr>')
        for day in calendar.weekheader(2).split():
            buff.write('<th scope="col">%s</th>' % day)
        buff.write('</tr>\n</thead>\n<tbody>')
        
        last_week_prev_month = calendar.monthcalendar(prevYear, prevMonth)[-1];
        first_week_next_month = calendar.monthcalendar(nextYear, nextMonth)[0];
        w = -1
        for week in calendar.monthcalendar(year, month):
            buff.write('\n<tr>')
            w = w+1
            d = -1
            for day in week:
                d = d+1
                
                # calc date and update CSS classes
                date[0:3] = [year, month, day]
                classes = 'day'
                if not day:
                    classes += ' adjacent_month'
                    if w == 0:
                        day = last_week_prev_month[d]
                        date[0:3] = [prevYear, prevMonth, day]
                    else:
                        day = first_week_next_month[d]
                        date[0:3] = [nextYear, nextMonth, day]
                else:
                    if day == curr_day:
                        classes += ' today'
                url = ''
                title = ''
                
                # check for milestone
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                duedate = time.mktime(tuple(date))
                cursor.execute("SELECT name FROM milestone WHERE due=%s", (duedate,))
                row = cursor.fetchone()
                if row:
                    milestone_name = row[0]
                    classes += ' milestone'
                    url = self.env.href.milestone(milestone_name)
                    title = 'Milestone: ' + milestone_name + ' - '
                    
                # check for wikipage with name specified in 'wiki_page_format'
                wiki = time.strftime(wiki_page_format, tuple(date))
                url = self.env.href.wiki(wiki)

                if wiki.find(":") >= 0 or wiki.startswith("/"):
                    url = self.env.href.wiki(wiki)
                    wiki = wiki.lstrip("/")
                else:
                    # Support relative paths; based on trac/wiki/formatter.py
                    rsc = get_relative_resource(formatter.resource, wiki)
                    wiki = rsc.id
                    url = get_resource_url(self.env, rsc, formatter.href)

                if WikiSystem(self.env).has_page(wiki):
                    classes += ' page'
                    title += 'Go to page %s' % wiki
                else:
                    url += "?action=edit"
                    title += 'Create page %s' % wiki
                    
                # buffer output
                buff.write('\n<td><a class="%(classes)s" href="%(url)s" title="%(title)s">%(day)s</a></td>' % {
                    'classes': classes.strip(),
                    'url': url,
                    'title': title.encode('utf-8'),
                    'day': day
                    })
            buff.write('\n</tr>')
        buff.write('\n</tbody>\n</table>\n')
        table = buff.getvalue()
        buff.close()
        return table
