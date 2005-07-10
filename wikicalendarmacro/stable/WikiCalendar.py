# Copyright (C) 2005 Matthew Good <matt@matt-good.net>
#
# "THE BEER-WARE LICENSE" (Revision 42):
# <matt@matt-good.net> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff.  If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.  Matthew Good
# (Beer-ware license written by Poul-Henning Kamp
#  http://people.freebsd.org/~phk/)
#
# Author: Matthew Good <matt@matt-good.net>

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

    buff = StringIO()

    date = [year, month] + [1] * 7

    buff.write('<table><caption>')
    buff.write(time.strftime('%B %Y', tuple(date)))
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
