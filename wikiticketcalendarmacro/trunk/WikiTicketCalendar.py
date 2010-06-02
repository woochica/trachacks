# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# Copyright (C) 2005 Jan Finell <finell@cenix-bioscience.com> 
# Copyright (C) 2007 Mike Comb <mcomb@mac.com> 
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

# Major revisions by Mike Comb <mcomb@mac.com> to display tickets, improve
# formatting and turn into a full page calendar.

import time
import calendar
import sys
from string import replace
from StringIO import StringIO
from trac.wiki.api import WikiSystem
from trac.util import *

revision="$Rev$"
url="$URL$"

# format:
#   WikiTicketCalendar([year,month,[showbuttons,[wiki_page_format]]])
#
#   displays a calendar, the days link to:
#     - milestones (day in bold) if there is one on that day
#     - a wiki page that has wiki_page_format (if exist)
#     - create that wiki page if it does not exist
#
# arguments: 
#   year, month = display calendar for month in year ('*' for current year/month)
#   showbuttons = true/false, show prev/next buttons
#   wiki_page_format = strftime format for wiki pages to display as link
#                      (if there is not a milestone placed on that day)
#                      (if exist, otherwise link to create page)
#                      default is "%Y-%m-%d"
#
# examples:
#     WikiTicketCalendar(2006,07)
#     WikiTicketCalendar(2006,07,false)
#     WikiTicketCalendar(*,*,true,Meeting-%Y-%m-%d)
#     WikiTicketCalendar(2006,07,false,Meeting-%Y-%m-%d)

def execute(hdf, txt, env):
    today = time.localtime()
    http_param_year = hdf.getValue("args.year", "")
    http_param_month = hdf.getValue("args.month", "")
    if txt == "":
        args = []
    else:
        args = txt.split(',', 3)
    
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

    # Can use this to change the day the week starts on, but this
    # is a system-wide setting
    calendar.setfirstweekday(calendar.SUNDAY)
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

    if showbuttons:
        # prev month link
        prevMonthURL = thispageURL+'?month=%d&year=%d' % (prevMonth, prevYear)
        buff.write('<a href="%s"><b>&lt;</b> </a>' % prevMonthURL)
        
    # the caption
    buff.write(time.strftime('<strong>%B %Y</strong>', tuple(date)))
    
    if showbuttons:
        # next month link
        nextMonthURL = thispageURL+'?month=%d&year=%d' % (nextMonth, nextYear)
        buff.write('<a href="%s"> <b>&gt;</b></a>' % nextMonthURL)
        
    buff.write('</caption>\n<thead><tr align="center">')
    
    for day in calendar.weekheader(2).split():
        buff.write('<th scope="col"><b>%s</b></th>' % day)
    buff.write('</tr></thead>\n<tbody>\n')

    for row in cal:
        buff.write('<tr align="right">')
        for day in row:
            if not day:
                buff.write('<td>&nbsp;</td>')
            else:
                # first check for milestone on that day
                db = env.get_db_cnx()
                cursor = db.cursor()
                # ugly way but i don't know how to set up a struct_time
                # (date as single numbers -> string -> time string parser -> struct_time -> mktime -> seconds
                duedateString = str(day) + "." + str(month) + "." + str(year)
                duedateStruct = time.strptime(duedateString, "%d.%m.%Y")
                duedatestamp = time.mktime(duedateStruct)
					
                dayString = str(day)
                monthString = str(month)
                yearString = str(year)
                
                buff.write('<td%(style)s width="110" valign="top"><b>%(day)s</b>' % {
						'day': day,
						'style': day == curr_day and ' style="background: #fbfbfb; border-color: #444444; color: #444; border-style:solid; border-width:1px;"' or ' style="background: #e5e5e5; border-color: #444444; color: #333; border-style:solid; border-width:1px;"',
						})
                
                if day < 10:
                	dayString = "0" + str(day)
                if month < 10:
                	monthString = "0" + str(month)
                yearString = yearString[2:4]
                
                duedate = monthString + "/" + dayString + "/" + yearString
                
                cursor.execute("SELECT name FROM milestone WHERE due=%s", (duedatestamp,))
                while (1):
                	row = cursor.fetchone()
                	if row == None:
                		buff.write('<br>')
                		break
                	else:
						name = row[0]
						url = env.href.milestone(name)
						buff.write('<table border="0" celpadding="0" cellspacing="0" width="110"><tr><td style="font-size: 9px; background: #f7f7f0; border: 1px solid #d7d7d7; border-bottom-color: #999;" align="left"><a href="%(url)s">* %(name)s</a></td></tr></table>' % {
							'name': name,
							'url': url,
							})
                cursor.execute("SELECT t.id,t.summary,t.keywords||' - '||t.owner,t.status,t.description FROM ticket t, ticket_custom tc where tc.ticket=t.id and tc.name='due_close' and tc.value=%s", (duedate,))

                #if row:
                while (1):
                	row = cursor.fetchone()
                	if row == None:
                		buff.write('</td>')
                		break
                	else:
						id = row[0]
						url = env.href.ticket(id)
						
						ticket = row[1]
						owner = row[2]
						status = row[3]
						description = "" #row[4]
						buff.write('<div style="%(style)s" align="left">%(ticket)s (<a href="%(url)s" title=\'%(description)s\' target="_blank">%(owner)s</a>)</div><p>' % {
								'url': url,
								'day': day,
								'ticket': ticket[0:100],
								'owner': owner,
								'style': status == 'closed' and 'font-size: 9px; color: #777777; text-decoration: line-through;' or 'font-size: 9px; color: #000000',
								'description': replace(description, "\'", "&#39;"),
								})

        buff.write('</tr>\n')

    buff.write('</tbody>\n</table>')
            
    table = buff.getvalue()
    buff.close()
    return table

