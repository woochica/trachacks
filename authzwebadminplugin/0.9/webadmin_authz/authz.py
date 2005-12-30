from trac.core import *
from trac.web.chrome import ITemplateProvider
from webadmin.web_ui import IAdminPageProvider
class AuthzManager(Component):
	implements(IAdminPageProvider, ITemplateProvider)

	#IAdminPageProvider methods
	def get_admin_pages(self, req):
		if req.perm.has_permission('TRAC_ADMIN'):
			yield ('general', 'General', 'authz', 'Authz Control')

	def process_admin_request(self, req, category, page, path_info):
		if req.method == 'POST':
			authzfile = file(self.config.get('trac', 'authz_file'), 'w')
			authzfile.write(req.args.get('Authz Contents'))
			authzfile.close()


		authzfile = file(self.config.get('trac', 'authz_file'), 'r')
		authz = ""
		authzlen = 0
		for line in authzfile.readlines():
			authz += line
			authzlen += 1

		authzfile.close()
		if authzlen < 20 :
			fieldlen = 24
		else:
			fieldlen = authzlen + 10

		req.hdf['admin.authz'] = {
			'contents': authz,
			'fieldlength': fieldlen
		}
		return 'admin_authz.cs', None

	#ITemplateProvider methods
	def get_templates_dirs(self):
		from pkg_resources import resource_filename
		return [resource_filename(__name__, 'templates')]
