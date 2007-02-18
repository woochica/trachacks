from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_script
from trac.web.main import _open_environment
from trac.util.html import html as tag

import os
import posixpath

class ProjectMenuModule(Component):
    
    implements(INavigationContributor, ITemplateProvider)
    
    # INavigationProvider methods
    def get_navigation_items(self, req):
        projects = []
        search_path, this_project = os.path.split(self.env.path)
        base_url, _ = posixpath.split(req.abs_href())
        
        for project in os.listdir(search_path):
            if project != this_project:
                proj_env = _open_environment(os.path.join(search_path, project))
                
                proj_elm = tag.OPTION(proj_env.project_name, value=posixpath.join(base_url, project))
                
                projects.append((proj_elm, proj_env.project_name))
        projects.sort(lambda a,b: cmp(a[1],b[1])) # Sort on the project names
        projects.insert(0, (tag.OPTION(self.env.project_name, value=''), None))
        
        add_script(req, 'projectmenu/projectmenu.js')
        yield 'metanav', 'projectmenu', tag.SELECT([e for e,_ in projects], name='projectmenu', id='projectmenu', onchange='return on_projectmenu_change();')
        
    def get_active_navigation_item(self, req):
        return ''
        
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('projectmenu', resource_filename(__name__, 'htdocs'))]
        
    def get_templates_dirs(self):
        #from pkg_resources import resource_filename
        #return [resource_filename(__name__, 'templates')]
        return []