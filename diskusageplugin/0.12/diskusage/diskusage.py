# -*- coding: utf-8 -*-
import os
import locale

from genshi.builder import tag

from trac.core import *
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider

class DiskUsage(Component):
    implements(IAdminPanelProvider, ITemplateProvider)
    
    def get_disk_usage(self, path):
        totalsize = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                totalsize += os.path.getsize(os.path.join(root, file))
        return totalsize
    
    def get_trac_disk_usage(self):
        trac_disk_usage = self.get_disk_usage(self.env.path)
        # separate number
        locale.setlocale(locale.LC_ALL, "")
        trac_disk_usage_string = locale.format("%d", trac_disk_usage, grouping=True)
        
        return trac_disk_usage_string
    
    def get_svn_disk_usage(self):
        svn_disk_usage = self.get_disk_usage(self.config.get('trac', 'repository_dir'))
        # separate number
        locale.setlocale(locale.LC_ALL, "")
        svn_disk_usage_string = locale.format("%d", svn_disk_usage, grouping=True)
        
        return svn_disk_usage_string
        
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__,'templates')]
    
    def get_htdocs_dirs(self):
        return []

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        """Return a list of available admin panels.
        
        The items returned by this function must be tuples of the form
        `(category, category_label, page, page_label)`.
        """
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('diskusage', 'Disk Usage', 'diskusage', 'Disk Usage')

    def render_admin_panel(self, req, category, page, path_info):
        """Process a request for an admin panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """
        req.perm.require('TICKET_ADMIN')
        svn_disk_usage = self.get_svn_disk_usage()
        trac_disk_usage = self.get_trac_disk_usage()
        data = {
            'trac_disk_usage': trac_disk_usage,
            'svn_disk_usage': svn_disk_usage
        }    
        
        return 'diskusage.html', data
