from types import ListType, StringTypes

from trac.core import *

from trac.perm import PermissionSystem, IPermissionPolicy, IPermissionGroupProvider
from trac.env import IEnvironmentSetupParticipant
from trac.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.ticket.report import ReportModule

from genshi.filters import Transformer
from genshi.filters.transform import StreamBuffer
from genshi.input import HTML

from pkg_resources import resource_filename

class PrivateReports(Component):

	group_providers = ExtensionPoint(IPermissionGroupProvider)

	implements(ITemplateStreamFilter, IEnvironmentSetupParticipant, IAdminPanelProvider, ITemplateProvider, IRequestFilter)

	# IRequestFilter 
	def pre_process_request(self, req, handler):
		if handler is not ReportModule(self.env):
			return handler	
			
		url = req.path_info	
		user = req.authname
		
		find = url.rfind('/')
		report_id= url[find+1:]
		
		try:
			report_id = int(report_id)
		except:
			return handler
		
		if self._has_permission(user,report_id):
			return handler
		else:
			raise TracError('You don\'t have the permission to access this report', 'No Permission')
		
	def post_process_request(self, req, template, data, content_type):
		return template, data, content_type
	
	# ITemplateProvider
	def get_htdocs_dirs(self):
		return []

	def get_templates_dirs(self):
		return [resource_filename(__name__, 'templates')]

	# IAdminPanelProvider
	def get_admin_panels(self, req):
		if req.perm.has_permission('TRAC_ADMIN'):
			yield ('privatereports', 'PrivateReports', 'privatereports', 'PrivateReports')

	def render_admin_panel(self, req, cat, page, path_info):
		if page == 'privatereports':

			reports = self._get_reports()

			data = {
				'reports': reports
			}

			if req.method == 'POST':

				report_id = req.args.get('report_id')
				try:
					report_id = int(report_id)
				except:
					req.redirect(self.env.href('/admin/privatereports/privatereports'))

				if req.args.get('add'):

					newpermission = req.args.get('newpermission')
					if newpermission == None or newpermission.isupper() == False:
						req.redirect(self.env.href('/admin/privatereports/privatereports'))

					report_permissions = self._get_report_permissions(report_id)
					
					if report_permissions or report_permissions == []:
						report_permissions.append(newpermission)
						self._alter_report_permissions(report_id, report_permissions)
					else:
						report_permissions = [newpermission]
						self._insert_report_permissions(report_id, report_permissions)

					data['report_permissions'] = report_permissions or ''
					data['show_report'] = report_id

				elif req.args.get('remove'):

					arg_report_permissions = req.args.get('report_permissions')
					if arg_report_permissions == None:
						req.redirect(self.env.href('/admin/privatereports/privatereports'))

					report_permissions = self._get_report_permissions(report_id)
					report_permissions = set(report_permissions)

					if type(arg_report_permissions) in StringTypes:
						toremove = set([arg_report_permissions])
					elif type(arg_report_permissions) == ListType:
						toremove = set(arg_report_permissions)
					else:
						req.redirect(self.env.href('/admin/privatereports/privatereports'))

					report_permissions = report_permissions - toremove

					self._alter_report_permissions(report_id, report_permissions)

					data['report_permissions'] = report_permissions or ''
					data['show_report'] = report_id

				elif req.args.get('show'):

					report_permissions = self._get_report_permissions(report_id)
					data['report_permissions'] = report_permissions or ''
					data['show_report'] = report_id

			else:
				report_permissions = self._get_report_permissions(reports[0][1])
				data['report_permissions'] = report_permissions or ''

			return 'admin_privatereports.html', data

	# IEnvironmentSetupParticipant
	def environment_created(self):
		db = self.env.get_db_cnx()
		if self.environment_needs_upgrade(db):
			self.upgrade_environment(db)

	def environment_needs_upgrade(self, db):
		cursor = db.cursor()
		try:
			cursor.execute('SELECT * FROM private_report')
			cursor.close ()
			return False
		except:
			cursor.connection.rollback()
			cursor.close ()
			return True

	def upgrade_environment(self, db):
		cursor = db.cursor()
		try:
			cursor.execute('CREATE TABLE private_report(report_id integer, permissions text)')
			cursor.close ()
			db.commit()
		except:
			cursor.connection.rollback()
			cursor.close ()

	# ITemplateStreamFilter
	def filter_stream(self, req, method, filename, stream, data):
		if not filename == 'report_list.html':
			return stream
			
		user = req.authname

		buffer = StreamBuffer()

		def check_report_permission():
			delimiter = '</tr>'

			reportstream = str(buffer)

			reports_raw = reportstream.split(delimiter)
			reportstream = ''

			for report in reports_raw:
				if report != None and len(report) != 0:

					# determine the report id
					s = report.find('/report/')
					if s == -1:
						continue

					e = report.find('\"',s)
					if e == -1:
						continue
					report_id = report[s+len('/report/'):e]

					if self._has_permission(user,report_id):
						reportstream += report

			return HTML(reportstream)

		return stream | Transformer('//tbody/tr') \
		.copy(buffer) \
		.replace(check_report_permission)

	# Internal
	def _has_permission(self, user, report_id):
		report_permissions = self._get_report_permissions(report_id)
		
		if report_permissions == None or report_permissions == []:
			return True
			
		perms = PermissionSystem(self.env)

		report_permissions = set(report_permissions)
		user_perm = set(perms.get_user_permissions(user))
		groups = set(self._get_user_groups(user))
		
		user_perm.update(groups)
		
		if report_permissions.intersection(user_perm) != set([]):
			return True
			
		return False
		
	def _get_user_groups(self, user):
		subjects = set([user])
		for provider in self.group_providers:
			subjects.update(provider.get_permission_groups(user) or [])

		groups = []
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		sql = "SELECT action FROM permission WHERE username = \'%s\'" % (user)
		cursor.execute(sql)
		rows = cursor.fetchall()
		for action in rows:
			if action[0].isupper():
				groups.append(action[0])
			
		return groups
	
	def _get_reports(self):
		db = self.env.get_db_cnx()

		cursor = db.cursor()

		sql = 'SELECT title,id FROM report'
		self.log.debug(sql)

		cursor.execute(sql)
		reports = cursor.fetchall()
		cursor.close ()

		return reports


	def _insert_report_permissions(self,report_id, permissions):
		db = self.env.get_db_cnx()

		permission_str = ''
		for permission in permissions:
			permission_str = permission_str + '|' + permission

		permission_str = permission_str[1:]

		cursor = db.cursor()

		sql = 'INSERT INTO private_report(report_id, permissions) VALUES(%d,\'%s\')' % \
		(int(report_id), str(permission_str))
		self.log.debug(sql)

		cursor.execute(sql)
		cursor.close ()
		db.commit()

	def _alter_report_permissions(self,report_id, permissions):
		db = self.env.get_db_cnx()

		permission_str = ''
		for permission in permissions:
			permission_str = permission_str + '|' + permission

		permission_str = permission_str[1:]

		cursor = db.cursor()

		sql = 'UPDATE private_report SET permissions = \'%s\' WHERE report_id=%d' % \
		(str(permission_str),int(report_id))
		self.log.debug(sql)

		cursor.execute(sql)
		cursor.close ()
		db.commit()

	def _get_report_permissions(self,report_id):
		db = self.env.get_db_cnx()

		cursor = db.cursor()

		sql = 'SELECT permissions FROM private_report WHERE report_id=%d' % \
		(int(report_id))
		self.log.debug(sql)

		cursor.execute(sql)
		try:
			permissions = cursor.fetchone()[0]
		except:
			permissions = None

		# no entry available
		if permissions == None:
			return None

		# no permission set but an existing entry
		if len(permissions) == 0:
			return []

		permissions = str(permissions)

		# list of permissions
		return permissions.split('|')
