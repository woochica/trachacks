from trac.core import *
from trac.admin.api import IAdminPanelProvider
from helpers import get_options, TeamCityQuery, TeamCityError
from trac.web.chrome import add_stylesheet, add_javascript
from trac.web import HTTPForbidden

class TeamCityAdmin(Component):
	implements(IAdminPanelProvider)
	
	def get_admin_panels(self,req):
		if req.perm.has_permission('TEAMCITY_ADMIN'):
			yield('teamcity','TeamCity','builds','Builds')

	def render_admin_panel(self,req,category,page,path_info):
		if not req.perm.has_permission('TEAMCITY_ADMIN'):
			raise HTTPForbidden('You are not allowed to configure TC plugin')
		if req.method == 'POST':
			options,errors = self._save_options(req.args)
			if not errors:
				# redirect here
				req.redirect(req.href(req.path_info))
		else:
			options,errors = get_options(self.config),[]
		tc = TeamCityQuery(options)
		url = "%s/httpAuth/app/rest/buildTypes" % options['base_url']
		# load builds from TC using REST API
		try:
			builds_xml = tc.xml_query(url)
		except TeamCityError,e: 
			errors.append("Fix base config options: %s" % e)
			t_data = {'options':options,'projects':{},'errors':errors}
			return 'teamcity_admin.html',t_data
		projects = {}
		for build in builds_xml.iterfind('buildType'):
			pr_name = build.attrib['projectName']
			pr_id = build.attrib['projectId']
			if pr_id not in projects:
				projects[pr_id] = {'id':pr_id,'name':pr_name,'checked':False,'builds':[]}
			btype_id = build.attrib['id']
			if btype_id in options.get('builds',[]):
				projects[pr_id]['checked']=True
			projects[pr_id]['builds'].append({
					'btype_id': btype_id,
					'btype_name': build.attrib['name'],
					'btype_url': build.attrib['webUrl'],
					'checked': btype_id in options.get('builds',[])
			})
		add_stylesheet(req,'teamcity/css/admin.css')
		add_javascript(req,'teamcity/js/admin.js')
		t_data = {'options':options,'projects':projects,'errors':errors}
		return 'teamcity_admin.html',t_data

	def _save_options(self, args):
		errors = []
		new_options = {}
		if args.get('base_url',False):
			if args['base_url'][-1] == '/': # remove trailing slash
				args['base_url'] = args['base_url'][:-1]
			new_options['base_url'] = args['base_url']
		else:
			errors.append('Base url is required')
		if args.get('username',False):
			new_options['username'] = args['username']
		else:
			errors.append('Username is required')
		if args.get('password',False):
			new_options['password'] = args['password']
		else:
			errors.append('Password is required')
		if args.get('builds',False):
			if type(args['builds']) is list:
				new_options['builds'] = args['builds']
			else: # only one build was specified
				new_options['builds'] = [args['builds']]
		else:
			# no builds was specified
			new_options['builds'] = []
		if args.get('cache_dir',False):
			new_options['cache_dir'] = args['cache_dir']
		if args.get('limit',False):
			try:
				new_options['limit'] = int(args['limit'])
			except Exception,e:
				errors.append("Invalid limit value: %s" % e)
		if not errors:
			for key,value in new_options.items():
				if type(value) is list:
					value = ",".join(value)
				self.config.set('teamcity',key,value)
			self.config.save()
		return new_options,errors
