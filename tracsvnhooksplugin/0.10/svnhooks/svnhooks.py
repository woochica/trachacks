from trac.core import *
from trac.web.chrome import ITemplateProvider
from webadmin.web_ui import IAdminPageProvider
import string
import os

SECTIONS = {
  'post-commit'        : '',
  'pre-commit'         : 'There is a bug in some versions of SVN connected to the pre-commit hook! By filling the form you *have* to enable the hook.',
  'post-revprop-change': '',
  'pre-revprop-change' : '',
  'start-commit'       : 'There is a bug in some versions of SVN connected to the start-commit hook! By filling the form you *have* to enable the hook.',
  'pre-lock'	       : '',
  'post-lock'          : '',
  'pre-unlock'         : '',
  'post-unlock'        : ''
}

class SVNHooksPlugin(Component):
    implements(ITemplateProvider, IAdminPageProvider)

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
    	    yield ('svn', 'Subversion', 'hooks', 'Hooks')

    def process_admin_request(self, req, cat, page, path_info):
        assert req.perm.has_permission('TRAC_ADMIN')

        sections = SECTIONS.keys()
	sections.sort()

        # catch selected section
	if req.method == 'POST' and req.args.get('sections'):
	  section = req.args.get('sections')
        else:
          section = sections[0]

        # validate section
        if section not in sections:
            raise TracError("Invalid section %s" % section)

        # get config vars
        repository_type = self.config.get('trac', 'repository_type').upper()
	repository_dir = self.config.get('trac', 'repository_dir') + os.sep + 'hooks'
        base_url = self.config.get('trac', 'base_url')
	project_name = self.config.get('project', 'name')
        smtp_default_domain = self.config.get('notification', 'smtp_default_domain')
	smtp_from = self.config.get('notification', 'smtp_from')
        smtp_replyto = self.config.get('notification', 'smtp_replyto')
	
	# repository type must be SVN
	if repository_type!='SVN':
	    raise TracError("Wrong repository_type %s in trac.ini" % repository_type)

        # test if repository_dir exists
	if not os.access(repository_dir,os.X_OK|os.W_OK|os.R_OK):
	    raise TracError("Can't access repository hook directory %s" % repository_dir)

        tmplfile = repository_dir + os.sep + section + '.tmpl'
        hookfile = repository_dir + os.sep + section

	# evaluate forms
	if req.method == 'POST':
          # Change status
	  if req.args.get('tooglestatus'):
	    if req.args.get('tooglestatus')==' Enable ':
              os.chmod(hookfile,0770)
	    else:
	      os.chmod(hookfile,0660)
	  if req.args.get('savehookfile'):
 	    current=req.args.get('current').strip().replace('\r', '')
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
	  elif req.args.get('addemail'):
	    if req.args.get('emails'):
	      emails = req.args.get('emails')
	      subject = req.args.get('subject')
	      mfilter = req.args.get('filter')
              try:
		current=""
	        try:
	          fp = open(hookfile,'r')
	 	  current = fp.read()
		  fp.close()
		except:
		  pass
	        fp = open(hookfile,'a')
		fp.writelines(os.linesep)
		if 'REPOS="$1"' not in current:
		  fp.writelines('REPOS="$1"'+os.linesep)
		if 'REV="$2"' not in current:
		  fp.writelines('REV="$2"'+os.linesep)
  	        fp.writelines('/usr/lib/subversion/hook-scripts/commit-email.pl "$REPOS" "$REV" \\'+os.linesep)
                if smtp_from:
		  fp.writelines('--from "'+smtp_from+'" \\'+os.linesep)
                if smtp_replyto:
		  fp.writelines('-r "'+smtp_replyto+'" \\'+os.linesep)
                if smtp_default_domain:
		  fp.writelines('-h "'+smtp_default_domain+'" \\'+os.linesep)
                if mfilter:
  		  fp.writelines('-m "'+mfilter+'" \\'+os.linesep)
		if subject:
		  fp.writelines('-s "'+subject+'" \\'+os.linesep)
		for email in emails.strip().split():
		  fp.writelines(email+' \\'+os.linesep)
		fp.writelines(os.linesep)
	        fp.close()
	      except:
	        raise TracError("Can't write repository hook %s" % hookfile)
	  elif req.args.get('addtrac'):
              try:
		current=""
	        try:
	          fp = open(hookfile,'r')
	 	  current = fp.read()
		  fp.close()
		except:
		  pass
	        fp = open(hookfile,'a')
		fp.writelines(os.linesep)
		if 'REPOS="$1"' not in current:
		  fp.writelines('REPOS="$1"'+os.linesep)
		if 'REV="$2"' not in current:
		  fp.writelines('REV="$2"'+os.linesep)
		if 'LOG=' not in current:
		  fp.writelines('LOG=`/usr/bin/svnlook log -r $REV $REPOS`'+os.linesep)
		if 'AUTHOR=' not in current:
		  fp.writelines('AUTHOR=`/usr/bin/svnlook author -r $REV $REPOS`'+os.linesep)
		if 'TRAC_ENV=' not in current:
		  fp.writelines('TRAC_ENV="'+self.env.path+'"'+os.linesep)
		if 'TRAC_URL=' not in current:
		  fp.writelines('TRAC_URL="'+base_url+'"'+os.linesep)
  	        fp.writelines('/usr/bin/python /usr/share/trac/contrib/trac-post-commit-hook \\'+os.linesep)
		fp.writelines('-p "$TRAC_ENV" \\'+os.linesep)
		fp.writelines('-r "$REV" \\'+os.linesep)
		fp.writelines('-u "$AUTHOR" \\'+os.linesep)
		fp.writelines('-m "$LOG" \\'+os.linesep)
		fp.writelines('-s "$TRAC_URL"'+os.linesep)
		fp.writelines(os.linesep)
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

        req.hdf['svnhooks.section'] = section
        req.hdf['svnhooks.sections'] = sections
        req.hdf['svnhooks.status'] = os.access(hookfile,os.X_OK)
        req.hdf['svnhooks.current'] = current
        req.hdf['svnhooks.note'] = SECTIONS[section]
	req.hdf['svnhooks.project_name'] = project_name
        req.hdf['svnhooks.description'] = description
	
        return 'svnhooks.cs', None


    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []
