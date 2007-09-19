from trac.core import *
from trac.web.chrome import ITemplateProvider
from webadmin.web_ui import IAdminPageProvider

import string
import os

__all__ = ['SVNHooksPlugin']

BUGMSG = """There is a bug in some versions of SVN connected to the 
this hook! By filling the form you *have* to enable the hook."""

SECTIONS = {
    'post-commit'        : False,
    'pre-commit'         : BUGMSG,
    'post-revprop-change': False,
    'pre-revprop-change' : False,
    'start-commit'       : BUGMSG,
    'pre-lock'           : False,
    'post-lock'          : False,
    'pre-unlock'         : False,
    'post-unlock'        : False
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
        repository_dir = self.config.get('trac', 'repository_dir')
        hooks_dir = self.config.get('trac', 'repository_hooks_dir') 
        if not hooks_dir:
            hooks_dir = repository_dir + os.sep + 'hooks'
        project_name = self.config.get('project', 'name')
        
        # repository type must be SVN
        if repository_type!='SVN':
            raise TracError("Wrong repository_type %s in trac.ini" \
                            % repository_type)
        
        # test if repository_dir exists
        if not os.access(hooks_dir, os.X_OK|os.R_OK):
            raise TracError("Can't access hook directory %s. " % hooks_dir + \
                            "You may set the option repository_hooks_dir " + \
                            "in the [trac] section in the trac.ini " + \
                            "configuration file to point to the right " + \
                            "location.")
        
        tmplfile = hooks_dir + os.sep + section + '.tmpl'
        hookfile = hooks_dir + os.sep + section
        
        # read out current hookfile
        current=""
        try:
            fp = open(hookfile,'r')
            current = fp.read()
            fp.close()
        except Exception:
            pass
        
        # evaluate forms
        if req.method == 'POST':
            # toogle file status
            if req.args.get('tooglestatus'):
                if req.args.get('tooglestatus')==' Enable ':
                    try:
                        os.chmod(hookfile,0770)
                    except Exception:
                        pass
                else:
                    try:
                        os.chmod(hookfile,0660)
                    except Exception:
                        pass
            # save file
            elif req.args.get('savehookfile'):
                current=req.args.get('current').strip().replace('\r', '')
                if current:
                    try:
                        fp = open(hookfile, 'w')
                        fp.write(current)
                        fp.close()
                    except Exception:
                        raise TracError("Can't write hook file %s" % hookfile)
                else:
                    try:
                        os.remove(hookfile)
                    except Exception:
                        pass
            # add e-mail hook
            elif req.args.get('addemail') and req.args.get('emails'):
                self._add_emailhook(req, hookfile, current)
            # add Trac hook
            elif req.args.get('addtrac'):
                self._add_trachook(req, hookfile, current)
        
        # read description from template file
        orig = ""
        try:
            fp = open(tmplfile,'r')
            orig = fp.readlines()
            fp.close()
        except Exception:
            pass
        description = " " + string.join(orig[4:])
        
        # read out current hookfile
        current=""
        try:
            fp = open(hookfile,'r')
            current = fp.read()
            fp.close()
        except Exception:
            pass
        
        req.hdf['svnhooks.section'] = section
        req.hdf['svnhooks.sections'] = sections
        req.hdf['svnhooks.status'] = os.access(hookfile,os.X_OK)
        req.hdf['svnhooks.current'] = current
        req.hdf['svnhooks.note'] = SECTIONS[section]
        req.hdf['svnhooks.project_name'] = project_name
        req.hdf['svnhooks.description'] = description

        return 'svnhooks.cs', None

    def _add_emailhook(self, req, hookfile, current):
        """
        Appends the subversion commit-email.pl script to the end of the 
        selected subversion hook file.
        """ 
        smtp_default_domain = self.config.get('notification', \
                                              'smtp_default_domain')
        smtp_from = self.config.get('notification', 'smtp_from')
        smtp_replyto = self.config.get('notification', 'smtp_replyto')
        emails = req.args.get('emails')
        subject = req.args.get('subject')
        mfilter = req.args.get('filter')
        # try to append hook
        try:
            fp = open(hookfile,'a')
            fp.writelines(os.linesep)
            if 'REPOS="$1"' not in current:
                fp.writelines('REPOS="$1"' + os.linesep)
            if 'REV="$2"' not in current:
                fp.writelines('REV="$2"' + os.linesep)
            fp.writelines('/usr/lib/subversion/hook-scripts/' + \
                          'commit-email.pl "$REPOS" "$REV" \\'+os.linesep)
            if smtp_from:
                fp.writelines('--from "' + smtp_from + '" \\' + os.linesep)
            if smtp_replyto:
                fp.writelines('-r "' + smtp_replyto + '" \\' + os.linesep)
            if smtp_default_domain:
                fp.writelines('-h "' + smtp_default_domain + '" \\' \
                              + os.linesep)
            if mfilter:
                fp.writelines('-m "' + mfilter + '" \\' + os.linesep)
            if subject:
                fp.writelines('-s "' + subject + '" \\' + os.linesep)
            for email in emails.strip().split():
                fp.writelines(email.strip() + ' \\' + os.linesep)
            fp.writelines(os.linesep)
            fp.close()
        except Exception:
            raise TracError("Can't write repository hook %s" % hookfile)

    def _add_trachook(self, req, hookfile, current):
        """
        Appends the trac-post-commit-hook script to the end of the selected
        subversion hook file.
        """
        base_url = self.config.get('trac', 'base_url')
        # try to append hook
        try:
            fp = open(hookfile, 'a')
            fp.writelines(os.linesep)
            if 'REPOS="$1"' not in current:
                fp.writelines('REPOS="$1"' + os.linesep)
            if 'REV="$2"' not in current:
                fp.writelines('REV="$2"' + os.linesep)
            if 'LOG=' not in current:
                fp.writelines('LOG=`/usr/bin/svnlook log -r $REV $REPOS`' \
                              + os.linesep)
            if 'AUTHOR=' not in current:
                fp.writelines('AUTHOR=`/usr/bin/svnlook author -r $REV ' + \
                              '$REPOS`' + os.linesep)
            if 'TRAC_ENV=' not in current:
                fp.writelines('TRAC_ENV="'+self.env.path+'"' + os.linesep)
            if 'TRAC_URL=' not in current:
                fp.writelines('TRAC_URL="'+base_url+'"' + os.linesep)
            fp.writelines('/usr/bin/python /usr/share/trac/contrib/' + \
                          'trac-post-commit-hook \\' + os.linesep)
            fp.writelines('-p "$TRAC_ENV" \\' + os.linesep)
            fp.writelines('-r "$REV" \\' + os.linesep)
            fp.writelines('-u "$AUTHOR" \\' + os.linesep)
            fp.writelines('-m "$LOG" \\' + os.linesep)
            fp.writelines('-s "$TRAC_URL"' + os.linesep)
            fp.writelines(os.linesep)
            fp.close()
        except Exception:
            raise TracError("Can't write repository hook %s" % hookfile)


    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)
        
        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []
