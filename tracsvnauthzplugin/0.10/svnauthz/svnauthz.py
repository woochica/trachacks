from trac.core import *
from trac.web.chrome import ITemplateProvider
from webadmin.web_ui import IAdminPageProvider
import os

class SVNAuthzPlugin(Component):
    implements(ITemplateProvider, IAdminPageProvider)

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
    	    yield ('svn', 'Subversion', 'authz', 'Permissions')

    def process_admin_request(self, req, cat, page, path_info):
        assert req.perm.has_permission('TRAC_ADMIN')
        
	# get default authz file from trac.ini
	authz_file = self.config.get('trac', 'authz_file')
	
	# test if authz file exists and is writable
        if not os.access(authz_file,os.W_OK|os.R_OK):
	    raise TracError("Can't access authz file %s" % authz_file)

        # evaluate forms
	if req.method == 'POST':
	  current=req.args.get('current').strip()
	  try:
	    fp = open(authz_file,'w')
	    current = fp.write(current)
	    fp.close()
	  except:
	    raise TracError("Can't write authz file %s" % authz_file)

        # read current authz file
	current = ""
	try:
	    fp = open(authz_file,'r')
	    current = fp.read()
	    fp.close() 
	except:
	    pass

	req.hdf['svnauthz.current'] = current

        return 'svnauthz.cs', None


    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
	return []