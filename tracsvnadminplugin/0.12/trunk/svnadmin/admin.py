# SVNAdmin plugin

import os.path
import sys

from genshi.builder import tag

from trac.admin import IAdminPanelProvider
from trac.config import ListOption
from trac.core import *
from trac.util import *
from trac.util import as_bool
from trac.util.compat import any
from trac.util.text import breakable_path, normalize_whitespace, print_table, printout
from trac.util.translation import _, tag_
from trac.web.chrome import ITemplateProvider, Chrome, add_notice, add_warning, add_stylesheet
from trac.versioncontrol import DbRepositoryProvider

from svnadmin.api import SvnRepositoryProvider

class SvnAdmin(Component):
    """Component providing svnadmin management of repositories."""
    
    implements(IAdminPanelProvider, ITemplateProvider)
    
    allowed_repository_dir_prefixes = ListOption('versioncontrol',
        'allowed_repository_dir_prefixes', '',
        doc="""Comma-separated list of allowed prefixes for repository
        directories when adding and editing repositories in the repository
        admin panel. If the list is empty, all repository directories are
        allowed. (''since 0.12.1'')""")

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if 'VERSIONCONTROL_ADMIN' in req.perm:
            yield ('svnadmin', _("SVNAdmin"), 'config', _("Configuration"))
            yield ('svnadmin', _("SVNAdmin"), 'repositories', _("Repositories"))
    
    def render_admin_panel(self, req, category, page, path_info):
        req.perm.require('VERSIONCONTROL_ADMIN')
        
        if page == 'config':
            return self._do_config(req, category, page)
        elif page == 'repositories':
            return self._do_repositories(req, category, page)
        
    def _do_config(self, req, category, page):
        parentpath = self.config.get('svnadmin', 'parent_path')
        client = self.config.get('svnadmin', 'svn_client_location')
        admin = self.config.get('svnadmin', 'svnadmin_location')
        
    	if req.method == 'POST' and req.args.get('save_settings'):
    	    parentpath = req.args.get('parentpath')
            client = req.args.get('client')
            admin = req.args.get('admin')
            
            self.config.set('svnadmin', 'parent_path', parentpath)
            self.config.set('svnadmin', 'svn_client_location', client)
            self.config.set('svnadmin', 'svnadmin_location', admin)
            self.config.save()
            add_notice(req, _('The settings have been saved.'))
        
    	data = {
    	    'parentpath': parentpath,
    	    'client': client,
    	    'admin': admin
    	}
        add_stylesheet(req, 'svnadmin/css/svnadmin.css')
        return 'config.html', data
    
    def _do_repositories(self, req, category, page):
        # Check that the setttings have been set.
        parentpath = self.config.get('svnadmin', 'parent_path')
        client = self.config.get('svnadmin', 'svn_client_location')
        admin = self.config.get('svnadmin', 'svnadmin_location')
        if not parentpath or not client or not admin:
            add_warning(req, _('You must provide settings before continuing.'))
            req.redirect(req.href.admin(category, 'config'))
        
        data = {}
        
        svn_provider = self.env[SvnRepositoryProvider]
        db_provider = self.env[DbRepositoryProvider]
        
        if req.method == 'POST':
            # Add a repository
            if svn_provider and req.args.get('add_repos'):
                name = req.args.get('name')
                dir = os.path.join(parentpath, name)
                if name is None or name == "" or not dir:
                    add_warning(req, _('Missing arguments to add a repository.'))
                elif self._check_dir(req, dir):
                    try:
                        svn_provider.add_repository(name)
                        db_provider.add_repository(name, dir, 'svn')
                        add_notice(req, _('The repository "%(name)s" has been '
                                          'added.', name=name))
                        resync = tag.tt('trac-admin $ENV repository resync '
                                        '"%s"' % name)
                        msg = tag_('You should now run %(resync)s to '
                                   'synchronize Trac with the repository.',
                                   resync=resync)
                        add_notice(req, msg)
                        cset_added = tag.tt('trac-admin $ENV changeset '
                                            'added "%s" $REV' % name)
                        msg = tag_('You should also set up a post-commit hook '
                                   'on the repository to call %(cset_added)s '
                                   'for each committed changeset.',
                                   cset_added=cset_added)
                        add_notice(req, msg)
                        req.redirect(req.href.admin(category, page))
                    except TracError, why:
                        add_warning(req, str(why))
            
            # Remove repositories
            elif svn_provider and req.args.get('remove'):
                sel = req.args.getlist('sel')
                if sel:
                    for name in sel:
                        svn_provider.remove_repository(name)
                        db_provider.remove_repository(name)
                    add_notice(req, _('The selected repositories have '
                                      'been removed.'))
                    req.redirect(req.href.admin(category, page))
                add_warning(req, _('No repositories were selected.'))

        # Find repositories that are editable
        repos = {}
        if svn_provider is not None:
            repos = svn_provider.get_repositories()
        
        # Prepare common rendering data
        data.update({'repositories': repos})
		
        add_stylesheet(req, 'svnadmin/css/svnadmin.css')
        return 'repositories.html', data

    def _check_dir(self, req, dir):
        """Check that a repository directory is valid, and add a warning
        message if not.
        """
        if not os.path.isabs(dir):
            add_warning(req, _('The repository directory must be an absolute path.'))
            return False
        prefixes = [os.path.join(self.env.path, prefix)
                    for prefix in self.allowed_repository_dir_prefixes]
        if prefixes and not any(util.is_path_below(dir, prefix)
                                for prefix in prefixes):
            add_warning(req, _('The repository directory must be located below one of the following directories: '
                               '%(dirs)s', dirs=', '.join(prefixes)))
            return False
        return True
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)
        """
        from pkg_resources import resource_filename
        return [('svnadmin', resource_filename(__name__, 'htdocs'))]