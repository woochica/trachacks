"""
Display list of ticket numbers in a box on the right side of the page.
The purpose of this macro is show related tickets compactly.
You can specify ticket number or report number which would be expanded
as ticket numbers. Tickets will be displayed as sorted and uniq'ed.

Example:
{{{
[[TicketBox(#1,#7,#31)]]               ... list of tickets
[[TicketBox(1,7,31)]]                  ... '#' char can be omitted
[[TicketBox({1})]]                     ... expand report result as ticket list
[[TicketBox([report:1])]]              ... alternate format of report
[[TicketBox([report:9?name=val])]]     ... report with dynamic variable
[[TicketBox({1),#50,{2},100)]]         ... convination of above
[[TicketBox(500pt,{1})]]               ... with box width as 50 point
[[TicketBox(200px,{1})]]               ... with box width as 200 pixel
[[TicketBox(25%,{1})]]                 ... with box width as 25%
[[TicketBox('Different Title',#1,#2)]] ... Specify title
[[TicketBox(\"Other Title\",#1,#2)]]     ... likewise
[[TicketBox('%d tickets',#1,#2)]]      ... embed ticket count in title
}}}

[wiki:TracReports#AdvancedReports:DynamicVariables Dynamic Variables] 
is supported for report. Variables can be specified like
{{{[report:9?PRIORITY=high&COMPONENT=ui]}}}. Of course, the special
variable '{{{$USER}}}' is available. The login name (or 'anonymous)
is used as $USER if not specified explicitly.
"""

## NOTE: CSS2 defines 'max-width' but it seems that only few browser
##       support it. So I use 'width'. Any idea?

import re
import string

## default style values
styles = { "background": "#",
           "width": "60%",
           }

def execute(hdf, txt, env):
	db = env.get_db_cnx()
	curs = db.cursor()
	option = {}
	for args in txt.split(";"):
		(key, val) = args.split(":")
		option[key] = val
	ul = []
	try:
		curs.execute("SELECT id, summary, resolution FROM ticket WHERE milestone='%s' AND keywords='%s'" % (option["milestone"], option["keyword"]))
		rows = curs.fetchall()
		for row in rows:
			if row[2]:
				cn="closed ticket"
			else:
				cn="new ticket"
			ul.append('<li>%s - <a class="%s" href="/cgi-bin/trac.cgi/ticket/%s" title="%s">%s</a></li>' % (row[1], cn, row[0], row[1], row[0]))
	except Exception, e:
		return 'error: %s %s' % (Exception, e)
	return '''
<fieldset class="ticketbox" style="background: #f7f7f0; width:80%%;">
	<legend>%s:</legend>
	<ul>
	%s
	</ul>
</fieldset>
''' % (option["keyword"], "\n".join(ul))
