# -*- coding: utf-8 -*-

import os
from trac.wiki.macros import WikiMacroBase
from trac.core import *
from StringIO import StringIO
from trac.config import Configuration
from pysqlite2 import dbapi2 as sqlite2
import cgi
import time
from trac.wiki.model import WikiPage

conf_path="/usr/local/share/trac/trac.main.ini"
db="/db/trac.db"
config = Configuration(os.path.join(conf_path))

#try: trac_path=config.get('Wstats','trac_path')
trac_path="/srv/trac/"

#try : trac_url=config.get('Wstats','trac_urls')
trac_url="/"

def create_struct( trac, mode , page ):
	url=trac_url+trac

	# Connect to database
	print "Debug ************************ Db is %s%s%s" %(trac_path, trac, db)
	try: dbase=sqlite2.connect(trac_path + trac + db)
	except:	return "<h1> Could Not Open database </h1>"
	cur=dbase.cursor()

	# Get new, closed and total tickets
	cur.execute('select count(id) from ticket where status!="closed";')
	new=cur.fetchone()
	new=int(new[0])

	cur.execute('select count(id) from ticket where status=="closed";')
	closed=cur.fetchone()
	closed=int(closed[0])

	cur.execute('select count(id) from ticket;')
	total=cur.fetchone()
	total=int(total[0])
	# Get lastest revision
	cur.execute("select * from revision limit 1 offset (select count(*) from revision) - 1 ")
	row=cur.fetchone()

	try:
		revision = "\n<br/>Lastest revision: <ul>\n <li>Author: %s</li>\n<li> Date:" % row[2]
		revision = revision +  time.strftime("%d %b %y",time.localtime(row[1])) + "</li>\n"
		revision = revision + "<li> Message: %s </li>\n</ul>\n" % row[3]
	except: revision=""

	if closed==total: style=" style=\"color:red;\"" 
	else: style=""

	# Print results
#	if mode==1:
	try: closedpercentage=closed * 100 / (new + closed)
	except: closedpercentage=0
	newpercentage = 100 - closedpercentage
	return "\n \
	<h2><a %s href=\"%s\"\>Trac %s</a></h2> \
	Tickets: %s <br/> \
	Open tickets: <a href=\"%s/query?status=assigned&status=needinfo&status=new&status=reopened&group=resolution&col=id&col=summary&col=status&col=type&col=priority&col=component&order=priority\"> %s (%s%%)</a> <br/>\
	Closed tickets: <a href=\"%s/query?status=closed\"> %s (%s%%)</a> \
	%s\
	\n" %(style,url,trac,total,url,new,newpercentage,url,closed,closedpercentage,revision)
#	else:
#		return """
#			<h2 >Trac: <a %s href="%s">%s</a> </h2>
#			Total: %d<br/>
#			Closed:%d <br/>
#			New: %d<br/>
#			<a href=%s>More Info</a><br/>%s<br/>
#		""" % (style,url,trac, total , closed , new, page, revision)

def print_header( trac ): return "<h1> %s </h1>" %trac

class WstatsMacro(WikiMacroBase):
	def expand_macro(self,formatter,name,args):
	        context = formatter.context
	        resource = context.resource
		f = cgi.FieldStorage()

		try: show=f['show']
		except: show=""

		page= "/wiki/" + WikiPage(self.env,resource).name  + "?show=" 

		if show != "":  return print_header(show) + create_struct( show, 1, page + show)
		else:
			IO=StringIO()
			one_month_time=time.time() - 30 * 86400 # Seconds of one month ago
			one_day_time=time.time() - 1 * 86400  # And yesterda
			today=[]
			yesterday=[]
			monthly=[]
			older=[]

			for traca in os.listdir('/srv/trac'): 
				mtime=os.stat(trac_path + traca + db).st_mtime # Mod date in seconds
				days=( (time.time() - mtime) / ( 1 * 86400))
				if days < 1: today.append(traca)
				else: 
					if days < 2: yesterday.append
					else:
						if days < 30: monthly.append(traca)
						else: older.append(traca)
			
			IO.write(print_header("Today"))
			for tracn in today: 
				a=create_struct( tracn , 0 , page + tracn )
				IO.write(a)

			IO.write(print_header("Yesterday"))
			for tracn in yesterday: 
				a=create_struct( tracn , 0 , page + tracn )
				IO.write(a)

			IO.write(print_header("Last Month"))
			for tracn in monthly: 
				a=create_struct( tracn , 0 , page + tracn )
				IO.write(a)

			IO.write(print_header("Really old"))
			for tracn in older: 
				a=create_struct( tracn , 0 , page + tracn )
				IO.write(a)

			return print_header("Main") + "<p>Active tracs, ordered by databse modification time</p>" + IO.getvalue()

