from trac.core import *
from trac.perm import IPermissionGroupProvider,PermissionSystem, IPermissionRequestor
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.web_ui import TicketModule

from trac.web.api import ITemplateStreamFilter, IRequestHandler, IRequestFilter
from genshi.builder import tag
from genshi.filters import Transformer
from genshi.filters.transform import StreamBuffer
from genshi.input import HTML

class PrivateComments(Component):
	group_providers = ExtensionPoint(IPermissionGroupProvider)
	implements(ITemplateStreamFilter, IEnvironmentSetupParticipant, IRequestHandler, IRequestFilter, IPermissionRequestor)
	
	# IPermissionRequestor methods
	def get_permission_actions(self):
		group_actions = [self.config.get('privatecomments','permission','PRIVATE_COMMENT_PERMISSION')] 
		return group_actions
	
	# IRequestHandler methods
	def pre_process_request(self, req, handler):
		if handler is not TicketModule(self.env):
			return handler	
		
		if req.method != 'POST':
			return handler
		
		# determine the ticket id
		url = req.path_info
		find = url.rfind('/')
		if find == -1 or find == 0:
			return handler
				
		ticket_id = url[find+1:]
		
		# determine if the request is an editing request, the comment id and if the comment should be private
		editing = -1
		comment_id = -1
		private = -1
		
		arg_list = req.arg_list
		for key,value in arg_list:
			if key == 'comment':
				editing = False
			elif key == 'edited_comment':
				editing = True
			elif key == 'cnum':
				comment_id = value
			elif key == 'cnum_edit':
				comment_id = value
			elif key == 'private_comment' and value == 'on':
				private = 1
				
			if editing != -1 and comment_id != -1 and private != -1:
				break
				
		if editing == -1 or comment_id == -1:
			return handler
			
		if private == -1:
			private = 0
		
		# finally update or insert a private_comment entry
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		
		try:
			if editing == True:
				sql = 'UPDATE private_comment SET private=%d WHERE ticket_id=%d AND comment_id=%d' % (int(private),int(ticket_id),int(comment_id))	
			elif editing == False:
				sql = 'INSERT INTO private_comment(ticket_id,comment_id,private) values(%d,%d,%d)' % (int(ticket_id),int(comment_id),int(private))
				
			self.log.debug(sql)
			
			cursor.execute(sql)
			cursor.close ()
			db.commit()
		except:
			cursor.close ()

		return handler

	def post_process_request(self, req, template, data, content_type):
		return template, data, content_type
	
	# IRequestFilter methods
	def match_request(self,req):
		return False
		
	def process_request(self,req):
		return None
	
	# IEnvironmentSetupParticipant methods
	def environment_created(self):
		db = self.env.get_db_cnx()
		if self.environment_needs_upgrade(db):
			self.upgrade_environment(db)
		
	def environment_needs_upgrade(self, db):
		cursor = db.cursor()
		
		if self.config.get('privatecomments','permission','') == '':
			return True
		
		try:
			cursor.execute('SELECT * FROM private_comment')
			cursor.close ()
			return False
		except:
			cursor.close ()
			return True
	
	def upgrade_environment(self, db):
		self.config.set('privatecomments','permission','PRIVATE_COMMENT_PERMISSION')
		self.config.save()
	
		try:
			cursor = db.cursor()
			cursor.execute('CREATE TABLE private_comment(ticket_id integer, comment_id integer, private tinyint)')
			cursor.close ()
			db.commit()
		except:
			return
	
	# ITemplateStreamFilter methods
	def filter_stream(self, req, method, filename, stream, data):
		if filename != 'ticket.html':
			return stream
		
		# determine the username of the current user
		user = req.authname
		
		# determine ticket id
		href = req.path_info
		find = href.rfind('/')
		if find == -1 or find == 0:
			return stream	
		ticket_id = int(href[find+1:])
		
		# determine if the user has the permission to see private comments
		perms = PermissionSystem(self.env)
		hasprivatepermission = perms.check_permission(self.config.get('privatecomments','permission','PRIVATE_COMMENT_PERMISSION'),user)
		
		buffer = StreamBuffer()
		
		def check_comments():
			delimiter = '<div xmlns="http://www.w3.org/1999/xhtml" class="change" id="trac-change-'
		
			commentstream = str(buffer)
			# split the commentstream to get single comments
			comments_raw = commentstream.split(delimiter)
			commentstream = ''
			
			for comment in comments_raw:
				if comment != None and len(comment) != 0:
					# determine comment id
					find = comment.find('">')
					if find == -1:
						continue
					comment_id = comment[:find]
					# concat the delimiter and the comment again
					comment_code = delimiter+comment
					# if the user has the permission to see the comment the commentcode will be appended to the commentstream
					comment_private = self._is_comment_private(ticket_id,comment_id)
					
					if comment_private:
						comment_code = comment_code.replace('<span class="threading">','<span class="threading"> <span class="private_comment_marker">this comment is private</span>')
					
					if hasprivatepermission or not comment_private:	
						commentstream = commentstream + comment_code	
			
			return HTML(commentstream)
			
		def checkbox_for_privatecomments():
			return tag(
						tag.span('Private Comment ', class_='private_comment_checkbox'),
						tag.input(type='checkbox', name='private_comment')
					)
		
		# filter all comments
		stream |= Transformer('//div[@class="change" and @id]') \
		.copy(buffer) \
		.replace(check_comments)
		
		# if the user has the private comment permission the checkboxes to change the private value will be added
		if hasprivatepermission:
			stream |= Transformer('//textarea[@name="edited_comment" and @class="wikitext trac-resizable" and @rows and @cols]') \
			.after(checkbox_for_privatecomments).end() \
			.select('//fieldset[@class="iefix"]') \
			.before(checkbox_for_privatecomments)
		
		return stream
	
	# internal methods
	def _is_comment_private(self,ticket_id,comment_id):
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		
		sql = 'SELECT private FROM private_comment WHERE ticket_id=%d AND comment_id=%d' % (int(ticket_id),int(comment_id))
		self.log.debug(sql)
		
		cursor.execute(sql)
		try:
			private = cursor.fetchone()[0]
		except:
			private = 0
			
		cursor.close ()
		
		if private == 1:
			return True
		else:
			return False
