from trac.core import *
from trac.util import Markup
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.wiki.formatter import wiki_to_html
from StringIO import StringIO
import time
#import re

class MapData(Component):
	implements(IRequestHandler, IPermissionRequestor)
	
	dates = []
	colours = []
	MAX_FONTSIZE = 25
	MIN_FONTSIZE = 10
	FONT_GRADIENT = 0.2
	
	# IRequestHandler methods
	def match_request(self, req):
		return req.path_info == '/mapdata'
	
    # IPermissionRequestor methods
	def get_permission_actions(self):
		return ['TICKET_VIEW','WIKI_VIEW','MILESTONE_VIEW']
	
	
	def process_request(self, req):
		req.perm.assert_permission('WIKI_VIEW')
		req.perm.assert_permission('MILESTONE_VIEW')
		req.perm.assert_permission('TICKET_VIEW')
		req.write(self.map_html(req))
	
	
	def getArgs(self, req):
		"""Parses arguments from AJAX"""
		args = req.args
		try:
			colour_count = int(args['colour_count'])
			self.colours = (args['colours']).split(',')
			i = 0
			self.dates = []
			while (i<=colour_count):
				self.dates.append(args['date'+str(i)])
				i+=1
			end_time = time.mktime(time.strptime(self.dates[0], '%d/%m/%Y'))
			start_time = time.mktime(time.strptime(self.dates[len(self.dates)-1], '%d/%m/%Y'))
		except:
			raise 'date error'
		
		if args.has_key('referer'):
			referer = args['referer']
		else:
			referer = '/wiki'
		if args.has_key('show_tickets'):
			show_tickets = 1
		else:
			show_tickets = 0
		if args.has_key('show_wiki'):
			show_wiki = 1
		else:
			show_wiki = 0
		if args.has_key('ticket_filter'):
			ticket_filter = args['ticket_filter']
		else:
			ticket_filter = 'active'
		if args.has_key('wiki_filter'):
			wiki_filter = args['wiki_filter']
		else:
			wiki_filter = 'all'
		if args.has_key('w_username'):
			w_username = args['w_username']
		else:
			w_username = ""
		if args.has_key('t_username'):
			t_username = args['t_username']
		else:
			t_username = ""
			
		return referer,start_time,end_time,show_tickets,ticket_filter,show_wiki,wiki_filter,w_username,t_username
	
		
	def map_html(self, req):
		hdf = req.hdf
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		
		referer,start_time,end_time,show_tickets,ticket_filter,show_wiki,wiki_filter,w_username,t_username = self.getArgs(req)
		
		output = '{{{ \n#!graphviz.dot \ndigraph G { \n\nlabeljust="left-justify";compound=true;ranksep=0.1;edge [arrowsize=0.6, color="lightgrey"]\ncolor=red;node [shape="box",style="filled", height=0.3, fontsize=10, fontcolor="#C20000"];\nrankdir="LR";\n'
		
		if show_wiki:
			# Compile Wiki Pages
			if (wiki_filter == 'all'):
				# Show all Wiki Pages except those created by Trac
				sql = "SELECT name,MAX(version) AS version,MAX(time) as time,1 FROM wiki WHERE time>%d AND time<%d AND author!='trac' GROUP BY name" % (start_time, end_time)
			elif (wiki_filter == 'others'):
				# Show Wiki Pages NOT edited by me
				sql = "SELECT w1.name,MAX(w1.version) AS version,MAX(w1.time) AS time,w2.name IS NULL AS others FROM wiki w1 LEFT JOIN (SELECT name FROM wiki WHERE author='%s') w2 ON w1.name=w2.name WHERE w1.time>%d AND w1.time<%d AND w1.author!='trac' GROUP BY w1.name" % (req.authname, start_time, end_time)
			elif (wiki_filter == 'mine'):
				# Wiki Pages edited by Me
				sql = "SELECT name,MAX(version) AS version,MAX(time) AS time,1 FROM wiki WHERE author='%s' AND time>%d AND time<%d GROUP BY name" % (req.authname, start_time, end_time)
			elif (wiki_filter == 'user'):
				# Wiki Pages edited by User <w_username>
				sql = "SELECT name,MAX(version) AS version,MAX(time) AS time,1 FROM wiki WHERE author='%s' AND time>%d AND time<%d GROUP BY name" % (w_username, start_time, end_time)
			
			cursor.execute(sql)
		
			sitemap = {}
			output += 'subgraph cluster1 {\nlabel = "Wiki Pages";color=lightgrey;\nrank=min;\n'
			now = time.time()
		
			for name,version,datetime,others in cursor:
				if others:
					#Flag for pages edited by me, checks the left join to see if it has been edited by me
					if (wiki_filter=='user'):
						#make Backlinks think I'm w_username
						sitemap[name] = self.getBacklinks(name, start_time, end_time, 'mine', w_username)
					else:
						sitemap[name] = self.getBacklinks(name, start_time, end_time, wiki_filter, req.authname)
					fontsize = min(self.MAX_FONTSIZE, self.MIN_FONTSIZE + version*self.FONT_GRADIENT)
					colour,fontcolour = self.getColour(datetime)
					output += '"%s" [URL="%s",color="%s",fontcolor="%s", fontsize=%d];\n' % (name, self.env.href.wiki(name), colour, fontcolour, fontsize)
			
			output += "\n"
		
			for page in sitemap:
				i = 0
				backlinks = sitemap[page]
				while i < len(backlinks):
					output += '"%s" -> "%s";\n' % (backlinks[i], page)
					i += 2 
				
			output += '}\n'
		
		if show_tickets:
			# Compile Tickets
			sql = "SELECT name,completed FROM milestone ORDER BY completed DESC"
			
			cursor.execute(sql)
			i = 1
			for name,completed in cursor:
				i+=1
				output += '\nsubgraph cluster%d {\nURL="%s";\nlabel = "%s";\ncolor=red;\nfontsize=10;\nrank=max;\n' % (i, self.env.href.milestone(name), name)
				if completed:
					output += 'style=filled;\nfillcolor=grey93;\n'
				if (ticket_filter=='user'):
					output += self.getTicketsByMilestone(name, start_time, end_time, 'mine', t_username)
				elif (ticket_filter=='useractive'):
					output += self.getTicketsByMilestone(name, start_time, end_time, 'myactive', t_username)
				else:
					output += self.getTicketsByMilestone(name, start_time, end_time, ticket_filter, req.authname)
				output += '}\n'
			output += '\nsubgraph cluster%d {\nlabel = "%s";\ncolor=red;\nfontsize=10;\nrank=max;\n' % (i+1, "No Milestone")
			if (ticket_filter=='user'):
				output += self.getTicketsByMilestone('', start_time, end_time, 'mine', t_username)
			elif (ticket_filter=='useractive'):
				output += self.getTicketsByMilestone('', start_time, end_time, 'myactive', t_username)
			else:
				output += self.getTicketsByMilestone('', start_time, end_time, ticket_filter, req.authname)
			output += '}\n'
			
		if show_tickets and show_wiki:
			# Get Links from tickets to wiki and from wiki to tickets
			if (ticket_filter == 'all'):
				sql = "SELECT id FROM ticket WHERE time>%d AND time<%d" % (start_time, end_time)
			elif (ticket_filter == 'active'):
				sql = "SELECT id FROM ticket WHERE status!='closed' AND time>%d AND time<%d" % (start_time, end_time)
			elif (ticket_filter == 'mine'):
				sql = "SELECT id FROM ticket WHERE (owner='%s' OR reporter='%s') AND time>%d AND time<%d" % (req.authname, req.authname, start_time, end_time)
			elif (ticket_filter == 'myactive'):
				sql = "SELECT id FROM ticket WHERE (owner='%s' OR reporter='%s') AND status!='closed' AND time>%d AND time<%d" % (req.authname, req.authname, start_time, end_time)
			elif (ticket_filter == 'user'):
				sql = "SELECT id FROM ticket WHERE (owner='%s' OR reporter='%s') AND time>%d AND time<%d" % (t_username, t_username, start_time, end_time)
			elif (ticket_filter == 'useractive'):
				sql = "SELECT id FROM ticket WHERE (owner='%s' OR reporter='%s') AND status!='closed' AND time>%d AND time<%d" % (t_username, t_username, start_time, end_time)
			cursor.execute(sql)
			
			for row in cursor: #links from the wiki to the tickets
				ticketlinks = []
				if (wiki_filter=='user'):
					ticketlinks = self.getTicketLinks(row[0], start_time, end_time, 'mine', w_username)
				else:
					ticketlinks = self.getTicketLinks(row[0], start_time, end_time, wiki_filter, req.authname)
				ticket = "Ticket%d" % (row[0])
				for wiki in ticketlinks:
					output += '"%s" -> %s;\n' % (wiki,ticket) 
			
			if (wiki_filter == "all"):
				sql = "SELECT DISTINCT name,1 FROM wiki WHERE author!='trac' AND time>%d AND time<%d ORDER BY name" % (start_time, end_time)
			elif (wiki_filter == "mine"):
				sql = "SELECT DISTINCT name,1 FROM wiki WHERE author='%s' AND time>%d AND time<%d ORDER BY name" % (req.authname, start_time, end_time)
			elif (wiki_filter == "others"):
				sql = "SELECT DISTINCT w1.name,w2.name IS NULL AS others FROM wiki w1 LEFT JOIN (SELECT DISTINCT name FROM wiki WHERE author='%s') w2 ON w1.name=w2.name WHERE w1.author!='trac' AND w1.time>%d AND w1.time<%d ORDER BY w1.name" % (req.authname, start_time, end_time)
			elif (wiki_filter == "user"):
				sql = "SELECT DISTINCT name,1 FROM wiki WHERE author='%s' AND time>%d AND time<%d ORDER BY name" % (w_username, start_time, end_time)
				
			cursor.execute(sql)
			
			for name,others in cursor: #links from the tickets to the wiki
				if others:
					#Flag for pages edited by me, checks the left join to see if it has been edited by me
					wikilinks = []
					if (ticket_filter=='user'):
						wikilinks = self.getWikiLinks(name, start_time, end_time, 'mine', t_username)
					elif (ticket_filter=='useractive'):
						wikilinks = self.getWikiLinks(name, start_time, end_time, 'myactive', t_username)
					else:
						wikilinks = self.getWikiLinks(name, start_time, end_time, ticket_filter, req.authname)
					for ticket in wikilinks:
						output += '%s -> "%s";\n' % (ticket, name)
		
		output += '} \n}}}\n'
		
		hdf.base_url = hdf.getValue('base_url', 'None')
		out = StringIO()	
		out.write(wiki_to_html(output, self.env, req))
		output = out.getvalue()
		
		return Markup(output)
	
	
	def getBacklinks (self, pagename, start_time, end_time, wiki_filter, authname):
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		if (wiki_filter == "all"):
			sql = "SELECT w1.name,1 FROM wiki w1, (SELECT name,MAX(version) AS version FROM wiki WHERE time>%d AND time<%d GROUP BY name) w2 WHERE w1.name=w2.name AND w1.version=w2.version AND w1.author!='trac' AND w1.text LIKE \'%%%s%%\' GROUP BY w1.name" % (start_time, end_time, pagename)
		elif (wiki_filter == "mine"):
			sql = "SELECT w1.name,1 FROM wiki w1, (SELECT name,MAX(version) AS version FROM wiki WHERE time>%d AND time<%d GROUP BY name) w2 WHERE w1.name=w2.name AND w1.version=w2.version AND w1.author='%s' AND w1.text LIKE \'%%%s%%\' GROUP BY w1.name" % (start_time, end_time, authname, pagename)
		elif (wiki_filter == "others"):
			sql = "SELECT w1.name,w2.name IS NULL AS others FROM wiki w1, (SELECT name,MAX(version) AS version FROM wiki WHERE time>%d AND time<%d GROUP BY name) w3 LEFT JOIN (SELECT name FROM wiki WHERE author='%s' GROUP BY name) w2 ON w3.name=w2.name WHERE w1.name=w3.name AND w1.version=w3.version AND w1.author!='trac' AND w1.text LIKE \'%%%s%%\' GROUP BY w1.name" % (start_time, end_time, authname, pagename)		
		cursor.execute(sql)
		
		backlinks = []		
		for name,others in cursor:
			if (name != pagename) and others:
				backlinks.append(name)
				backlinks.append(self.env.href.wiki(name))
				
		return backlinks
	
	# Links to Wiki pages from Tickets
	def getWikiLinks (self, pagename, start_time, end_time, ticket_filter, authname):
			db = self.env.get_db_cnx()
			cursor = db.cursor()
			
			if (ticket_filter == 'all'):
				sql = "SELECT id FROM ticket WHERE time>%d AND time<%d AND description LIKE '%%%s%%' UNION SELECT ticket FROM ticket_change WHERE newvalue LIKE '%%%s%%' AND time>%d AND time<%d GROUP BY ticket" % (start_time,end_time,pagename, pagename, start_time, end_time)
			elif (ticket_filter == 'active'):
				sql = "SELECT id FROM ticket WHERE status!='closed' AND description LIKE '%%%s%%' AND time>%d AND time<%d UNION SELECT t1.ticket FROM ticket_change t1, (SELECT id FROM ticket WHERE status!='closed') t2 WHERE t1.ticket=t2.id AND newvalue LIKE '%%%s%%' AND t1.time>%d AND t1.time<%d" % (pagename,start_time,end_time,pagename,start_time,end_time)
			elif (ticket_filter == 'mine'):
				sql = "SELECT id FROM ticket WHERE (owner='%s' OR reporter='%s') AND description LIKE '%%%s%%' AND time>%d AND time<%d UNION SELECT t1.ticket FROM ticket_change t1, (SELECT id FROM ticket WHERE owner='%s' OR reporter='%s') t2 WHERE t1.ticket=t2.id AND t1.newvalue LIKE '%%%s%%' AND t1.time>%d AND t1.time<%d" % (authname,authname,pagename,start_time,end_time,authname,authname,pagename,start_time,end_time)
			elif (ticket_filter == 'myactive'):
				sql = "SELECT id FROM ticket WHERE status!='closed' AND (owner='%s' OR reporter='%s') AND description LIKE '%%%s%%' AND time>%d AND time<%d UNION SELECT t1.ticket FROM ticket_change t1, (SELECT id FROM ticket WHERE (owner='%s' OR reporter='%s') AND status!='closed') t2 WHERE t1.ticket=t2.id AND t1.newvalue LIKE '%%%s%%' AND t1.time>%d AND t1.time<%d" % (authname,authname,pagename,start_time,end_time,authname,authname,pagename,start_time,end_time)
			
			cursor.execute(sql)
			wikilinks = []
			for row in cursor:
				name = "Ticket%d" % row[0]
				wikilinks.append(name)
			
			return wikilinks
	
	# Links to tickets from Wiki Pages
	def getTicketLinks (self, ticketnumber, start_time, end_time, wiki_filter, authname):
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		database = self.config.get('trac', 'database')
		if (wiki_filter == "all"):
			sql = "SELECT w1.name,1 FROM wiki w1, (SELECT name,MAX(version) AS version FROM wiki WHERE time>%d AND time<%d GROUP BY name) w2 WHERE w1.name=w2.name AND w1.version=w2.version AND w1.author!='trac' " % (start_time, end_time)
		elif (wiki_filter == "mine"):
			sql = "SELECT w1.name,1 FROM wiki w1, (SELECT name,MAX(version) AS version FROM wiki WHERE time>%d AND time<%d GROUP BY name) w2 WHERE w1.name=w2.name AND w1.version=w2.version AND w1.author='%s' " % (start_time, end_time, authname)
		elif (wiki_filter == "others"):
			sql = "SELECT w1.name,w2.name IS NULL AS others FROM wiki w1, (SELECT name,MAX(version) AS version FROM wiki WHERE time>%d AND time<%d GROUP BY name) w3 LEFT JOIN (SELECT name FROM wiki WHERE author='%s' GROUP BY name) w2 ON w3.name=w2.name WHERE w1.name=w3.name AND w1.version=w3.version AND w1.author!='trac' " % (start_time, end_time, authname)
			
		if ticketnumber and database.startswith('mysql:'):
			sql += 'AND (w1.text REGEXP \'.*ticket:%d[^0-9].*\' ' % ticketnumber	
			sql += 'OR w1.text REGEXP \'.*#%d[^0-9].*\') ' % ticketnumber	
		elif ticketnumber and database.startswith('sqlite:'):
			sql += 'AND (w1.text GLOB \'*ticket:%d[^0-9]*\' ' % ticketnumber	
			sql += 'OR w1.text GLOB \'*#%d[^0-9]*\') ' % ticketnumber
		
		sql += "GROUP BY w1.name"
		
		cursor.execute(sql)
		
		ticketlinks = []
		
		for name,others in cursor:
			if others:
				ticketlinks.append(name)
			
		return ticketlinks
	
	
	def getTicketsByMilestone (self, milestone, start_time, end_time, ticket_filter, authname):
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		cursor2 = db.cursor()
			
		output = ""
		
		if (ticket_filter == 'all'):
			sql = "SELECT t.id,MAX(tc.time),t.owner,t.status,tc.field FROM ticket_change tc, (SELECT id,owner,status FROM ticket WHERE milestone='%s') t WHERE tc.ticket=t.id AND tc.time>%s AND tc.time<%s GROUP BY t.id UNION SELECT id,time,owner,status,1 FROM ticket WHERE milestone='%s' AND time>%s AND time<%s GROUP BY id" % (milestone, start_time, end_time, milestone, start_time, end_time)
		elif (ticket_filter == 'active'):
			sql = "SELECT t.id,MAX(tc.time),t.owner,t.status,tc.field FROM ticket_change tc, (SELECT id,owner,status FROM ticket WHERE milestone='%s' AND status!='closed') t WHERE tc.ticket=t.id AND tc.time>%s AND tc.time<%s GROUP BY t.id UNION SELECT id,time,owner,status,1 FROM ticket WHERE status!='closed' AND milestone='%s' AND time>%s AND time<%s GROUP BY id" % (milestone, start_time, end_time, milestone, start_time, end_time)
		elif (ticket_filter == 'mine'):
			sql = "SELECT t.id,MAX(tc.time),t.owner,t.status,tc.field FROM ticket_change tc, (SELECT id,owner,status FROM ticket WHERE milestone='%s' AND (owner='%s' OR reporter='%s')) t WHERE tc.ticket=t.id AND tc.time>%s AND tc.time<%s GROUP BY t.id UNION SELECT id,time,owner,status,1 FROM ticket WHERE milestone='%s' AND (owner='%s' OR reporter='%s') AND time>%s AND time<%s GROUP BY id" % (milestone, authname, authname, start_time, end_time, milestone, authname, authname, start_time, end_time)
		elif (ticket_filter == 'myactive'):
			sql = "SELECT t.id,MAX(tc.time),t.owner,t.status,tc.field FROM ticket_change tc, (SELECT id,owner,status FROM ticket WHERE milestone='%s' AND (owner='%s' OR reporter='%s') AND status!='closed') t WHERE tc.ticket=t.id AND tc.time>%s AND tc.time<%s GROUP BY t.id UNION SELECT id,time,owner,status,1 FROM ticket WHERE milestone='%s' AND (owner='%s' OR reporter='%s') AND time>%s AND time<%s AND status!='closed' GROUP BY id" % (milestone, authname, authname, start_time, end_time, milestone, authname, authname, start_time, end_time)
			
		if (milestone==''):
			sql = sql.replace("milestone=''", "(milestone='' OR milestone is NULL)")
		
		cursor.execute(sql)
		tickets=[]
		now = time.time()
		for num,datetime,owner,status,field in cursor:
			name = "Ticket%d" % (num)
			if (name in tickets): #already done
				continue
			tickets.append(name)
			# get ticket change information
			cursor2.execute('SELECT COUNT(ticket) FROM ticket_change WHERE ticket=%d and time<%d ORDER BY time DESC' % (num,end_time))
			edits = cursor2.fetchone()[0]
			fontsize = min(self.MAX_FONTSIZE, self.MIN_FONTSIZE + edits*self.FONT_GRADIENT)
			fillcolour,fontcolour = self.getColour(datetime)
			colour = 'white'
			if status == 'closed':
				colour = 'red'
			output += '%s [shape="record", label="{%s|%s}", URL="%s", color="%s", fillcolor="%s", fontcolor="%s", fontsize=%d];\n' % (name, name, owner, self.env.href.ticket(num), colour, fillcolour, fontcolour, fontsize) #define tickets in cluster
			
		output += 'edge[style="dotted", arrowhead="none"];\n'
		output += "->".join(tickets)
		output += "\n"
		
		return output
	
	
	#Returns the appropriate colour gradient for the time, based on the maximum and minimum times
	def getColour(self, datetime):
		i = 0
		while (i<len(self.colours)):
			if ((datetime<=time.mktime(time.strptime(self.dates[i], '%d/%m/%Y'))) and (datetime>time.mktime(time.strptime(self.dates[i+1], '%d/%m/%Y')))):
				return ('#'+self.colours[i]),'#FFFFFF'
			i+=1
		return ('#'+self.colours[len(self.colours)-1]),'#FFFFFF'
	
		



		
