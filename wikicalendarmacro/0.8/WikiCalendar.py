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

import time
import calendar
from cStringIO import StringIO

cell_template = '<td%(style)s><a href="%(url)s"%(class)s>%(day)s</a></td>'

def execute(hdf, fmt, env):
    today = time.localtime()
    year = int(hdf.getValue("args.year", str(today.tm_year)))
    month = int(hdf.getValue("args.month", str(today.tm_mon)))
    curr_day = None
    if year == today.tm_year and month == today.tm_mon:
        curr_day = today.tm_mday

    # Can use this to change the day the week starts on, but this
    # is a system-wide setting
    #calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(year, month)


    date = [year, month] + [1] * 7

    # url to the current page (used in the navigation links)
    thispageURL = env.href.wiki(hdf.getValue('wiki.page_name', ''))
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

    # building the output
    buff = StringIO()
    buff.write('<table><caption>')

    # prev month link
    prevMonthURL = thispageURL+'?month=%d&year=%d' % (prevMonth, prevYear)
    buff.write('<a href="%s">&lt; </a>' % prevMonthURL)
    # the caption
    buff.write(time.strftime('%B %Y', tuple(date)))
    # next month link
    nextMonthURL = thispageURL+'?month=%d&year=%d' % (nextMonth, nextYear)
    buff.write('<a href="%s"> &gt;</a>' % nextMonthURL)
    buff.write('</caption>\n<thead><tr align="center">')
    
    for day in calendar.weekheader(2).split():
        buff.write('<th scope="col">%s</th>' % day)
    buff.write('</tr></thead>\n<tbody>\n')

    for row in cal:
        buff.write('<tr align="right">')
        for day in row:
            if not day:
                buff.write('<td>&nbsp;</td>')
            else:
                date[2] = day
                wiki = time.strftime(fmt, tuple(date))
                exists = env._wiki_pages.has_key(wiki)
                url = env.href.wiki(wiki)
                if not exists:
                    url += "?action=edit"
                buff.write(cell_template % {
                        'url': url,
                        'day': day,
                        'style': day == curr_day and ' style="border: 1px solid #b00;"' or '',
                        'class': not exists and ' class="missing"' or '',
                        })

        buff.write('</tr>\n')

    buff.write('</tbody>\n</table>')
            
    table = buff.getvalue()
    buff.close()
    return table

