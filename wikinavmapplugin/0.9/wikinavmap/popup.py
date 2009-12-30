from trac.core import *
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.util.datefmt import pretty_timedelta
from time import time, localtime, strftime

class MapPopupFiller(Component):
	implements(IRequestHandler, IPermissionRequestor)
	"""The PopupFiller class."""
	
	# IRequestHandler methods
	def match_request(self, req):
		return req.path_info == '/mappopup'
	
	# IPermissionRequestor methods
	def get_permission_actions(self):
		return ['TICKET_VIEW','WIKI_VIEW','MILESTONE_VIEW']
	
	def format_date(self, datetime):
		return strftime('%d/%m/%Y', localtime(datetime))
	
	def format_datetime(self, datetime):
		return strftime('%d/%m/%Y %H:%M', localtime(datetime))
	
	#Defines what is printed in the popup box
	def process_request(self, req):
		req.perm.assert_permission('WIKI_VIEW')
		req.perm.assert_permission('MILESTONE_VIEW')
		req.perm.assert_permission('TICKET_VIEW')
		name = req.args["node_title"]
		req.send_response(200)
		req.send_header('Content-Type', 'text/html')
		req.end_headers()
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		title = "Data not found"
		if name.startswith("{Ticket") or name.startswith("Ticket"):
			#it's a ticket
			if (name.startswith("{Ticket")):
				ticket = name[len("{Ticket"):name.index("|")]
			else:
				ticket = name[len("Ticket"):]
			sql = "SELECT t.id,t.type,t.time,tc.time,tc.author,t.component,t.summary,t.owner,t.reporter,t.status,t.resolution FROM ticket t INNER JOIN ticket_change tc ON t.id=tc.ticket WHERE t.id=%s order by tc.time desc" % ticket
			cursor.execute(sql)
			edits = cursor.rowcount + 1
			if not cursor.rowcount:
				sql = "SELECT id,type,time,time,owner,component,summary,owner,reporter,status,resolution FROM ticket WHERE id=%s" % ticket
				cursor.execute(sql)
			#row = cursor.fetchone()
			for num,ttype,created,lastedited,lastauthor,component,summary,owner,reporter,status,resolution in cursor:
				title = '<div id="popuptop">%s</div><div id="popupbottom"><strong>Edits:</strong> %d<br/><strong>Created:</strong><br/><em>%s ago (%s)</em><br/><strong>Last edited by %s</strong><br/><em>%s ago (%s)</em></strong><br/><strong>Type:</strong> %s<br/><strong>Component:</strong> %s<br/><strong>Owner:</strong> %s<br/><strong>Reporter:</strong> %s<br/><strong>Status:</strong> %s<br/>' % (summary, edits, pretty_timedelta(created), self.format_datetime(created), lastauthor, pretty_timedelta(lastedited), self.format_datetime(lastedited), ttype, component,owner,reporter,status)
				if (status=='closed'):
					title += '<strong>Resolution:</strong> %s<br/>' % resolution
				title += '</div>'
				break
		else:
			#Could be a wiki or a milestone
			sql = "SELECT name,version,time,author FROM wiki WHERE name='%s' order by time desc" % name
			cursor.execute(sql)
			#row = cursor.fetchone()
			found = False
			i = 0
			for name,version,datetime,author in cursor:
				lastedited = datetime
				if not found:
					title = '<div id="popuptop">%s</div><div id="popupbottom"><strong>Edits:</strong> %d<br/><strong>Last edited by %s</strong><br/><em>%s ago (%s)</em><br/><strong>Previous 3 Authors:</strong><br/>' % (name, version, author, pretty_timedelta(datetime), self.format_datetime(datetime))
					found = True
				elif (i<4):
					# Get list of previous 3 authors
					title += '%s <em>(%s ago)</em><br/>' % (author, pretty_timedelta(datetime))
				else:
					data = cursor.fetchall()
					if (len(data)>0):
						name,version,datetime,author = data[len(data)-1]
					title += '<strong>Created:</strong><br/><em>%s ago (%s)</em><br/></div>' % (pretty_timedelta(datetime), self.format_datetime(datetime))
					i+=1
					break
				i+=1
			if (i<=4 and found):
				title+= '<strong>Created:</strong><br/><em>%s ago (%s)</em><br/></div>' % (pretty_timedelta(lastedited), self.format_datetime(lastedited))
					
			if not found:
				#try a milestone
				sql = "SELECT name,due,completed FROM milestone WHERE name='%s'" % name
				cursor.execute(sql)
				for name,due,completed in cursor:
					completed_str = "Not completed"
					today = time()
					ago = ""
					if (today > due):
						ago = "ago "
						due += 86400						
					if completed:
						completed_str = "Completed"
					title = '<div id="popuptop">%s</div><div id="popupbottom"><strong>Due:</strong> <em>%s %s(%s)</em><br/><strong>%s</strong><br/></div>' % (name, pretty_timedelta(due), ago, self.format_date(due), completed_str)
					break
		
		req.write(title)
	

