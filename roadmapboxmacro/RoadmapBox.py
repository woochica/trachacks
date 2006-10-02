"""

Display a box with tickets concercing a certain Milestone AND Keyword.
We use tagging to group certain keywords together based on featureset, 
since they might fall in different components. This is ideal in the
Roadmap display, since it shows nice summary boxes of all open/closed 
tickets by keyword. 

Syntax:

[[RoadmapBox(keyword:Quickies;milestone:02-corecleanup)]]
[[RoadmapBox(keyword:Bugfixes;milestone:02-corecleanup)]]
[[RoadmapBox(keyword:Other;milestone:02-corecleanup)]]

Created by: frido.ferdinand@gmail.com
Based on: TicketBox

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
