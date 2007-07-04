from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet
from webadmin.web_ui import IAdminPageProvider
from trac.config import Option
import string
import os

SECTIONS = {
  'post-commit'        : '',
  'pre-commit'         : 'There is a bug in some versions of SVN connected to the pre-commit hook! By filling the form you *have* to enable the hook.',
  'post-revprop-change': '',
  'pre-revprop-change' : '',
  'start-commit'       : 'There is a bug in some versions of SVN connected to the start-commit hook! By filling the form you *have* to enable the hook.'
}

class SVNHooksPlugin(Component):
    implements(ITemplateProvider, IAdminPageProvider)

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
	    for section in SECTIONS.keys():
		yield ('svn', 'SVN Hooks', section, section)

    def process_admin_request(self, req, cat, page, path_info):
        assert req.perm.has_permission('TRAC_ADMIN')
        if page not in SECTIONS.keys():
            raise TracError("Invalid section %s" % page)

        repository_type = self.config.get('trac', 'repository_type').upper()
	repository_dir = self.config.get('trac', 'repository_dir') + os.sep + 'hooks'
	
	# repository type must be SVN
	if repository_type!='SVN':
	    raise TracError("Wrong repository_type %s in trac.ini" % repository_type)

        # test if repository_dir exists
	if not os.access(repository_dir,os.X_OK|os.W_OK|os.R_OK):
	    raise TracError("Can't access repository hook directory %s" % repository_dir)

        tmplfile = repository_dir + os.sep + page + '.tmpl'
        hookfile = repository_dir + os.sep + page

	# evaluate forms
	if req.method == 'POST':
          # Change status
	  if req.args.get('status'):
	    if req.args.get('status')==' Enable ':
              os.chmod(hookfile,0770)
	    else:
	      os.chmod(hookfile,0660)
	  if req.args.get('apply'):
	    if req.args.get('apply')==' Apply ':
 	      current=req.args.get('current').strip()    
              if current:
	        try:
 	          fp = open(hookfile,'w')
  	          fp.write(current)
	          fp.close()
	        except:
	          raise TracError("Can't write repository hook %s" % hookfile)
	      else:
	        try:
		  os.remove(hookfile)
		except:
		  pass
	  elif req.args.get('add'):
	    if req.args.get('add')==' Add ' and req.args.get('emails'):
	      emails = req.args.get('emails')
	      subject = req.args.get('subject')
	      mfilter = req.args.get('filter')
              try:
	        fp = open(hookfile,'a')
  	        fp.writelines('/usr/lib/subversion/hook-scripts/commit-email.pl "$REPOS" "$REV" \\\n')
                if mfilter:
  		  fp.writelines('-m "'+mfilter+'" \\\n')
		if subject:
		  fp.writelines('-s "'+subject+'" \\\n')
		for email in emails.strip().split():
		  fp.writelines(email+' \\\n')
		fp.writelines('\n')
	        fp.close()
	      except:
	        raise TracError("Can't write repository hook %s" % hookfile)
	      

        # read current hook file + get status
	current = ""
	try:
          fp = open(hookfile,'r')
  	  current = fp.read()
	  fp.close()
        except:
          pass
	  
        # read description from hook tmpl file
	orig = ""
        description = ""
        try:
          fp = open(tmplfile,'r')
  	  orig = fp.readlines()
	  fp.close()
	  description = " " + string.join(orig[4:])
        except:
          pass

        req.hdf['svnhooks.section'] = page
        req.hdf['svnhooks.status'] = os.access(hookfile,os.X_OK)
        req.hdf['svnhooks.current'] = current
        req.hdf['svnhooks.note'] = SECTIONS[page]
        req.hdf['svnhooks.description'] = description
	
        return 'svnhooks.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('svnhooks', resource_filename(__name__, 'htdocs'))]
