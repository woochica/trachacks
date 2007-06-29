# Created by Noah Kantrowitz on 2007-04-09.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.web.api import IRequestHandler
from trac.web.main import dispatch_request, _open_environment
from trac.web.chrome import INavigationContributor
from trac.perm import PermissionCache
from trac.util.text import to_unicode
from trac.util.html import html as tag

import os
import os.path
import copy

class TracForgeDispatcherModule(Component):
    """A request handler to dispatch /projects as if it were a TRAC_ENV_PARENT_DIR folder."""

    implements(IRequestHandler, INavigationContributor)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/projects')

    def process_request(self, req):
        path_info = req.path_info[10:]
        
        if path_info:
            project = path_info.split('/', 1)[0]
            
            # Check that we aren't trying to recurse (possible link loop)
            if project == os.path.basename(self.env.path):
                req.redirect(req.href())
                
            # Assert permissions on the desination environment
            project_path = os.path.join(os.path.dirname(self.env.path), project)
            try:
                project_env = _open_environment(project_path)
            except IOError:
                raise TracError('No such project "%s" at %s'% (project,project_path))
            project_perm = PermissionCache(project_env, req.authname)
            project_perm.assert_permission('PROJECT_VIEW')
            
            return self._send_project(req, path_info)
        else:
            return self._send_index(req)
            
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'projects'

    def get_navigation_items(self, req):
        yield 'mainnav', 'projects', tag.a('Projects', href=req.href.projects())
            
    # Internal methods
    def _send_project(self, req, path_info):
        start_response = req._start_response
        environ = copy.copy(req.environ)
        
        environ['SCRIPT_NAME'] = req.href.projects()
        environ['PATH_INFO'] = path_info
        print 'setting parent dir to', os.path.dirname(self.env.path)
        
#        environ['TRAC_ENV_PARENT_DIR'] = os.path.dirname(self.env.path)
#        if 'TRAC_ENV' in environ:
#            del environ['TRAC_ENV']

# The above incantation didn't work on the development server.  If we have
# problems serving subprojects on the real server, though, we may need to
# reinstate it along with the replacement below.

        environ['trac.env_parent_dir'] = os.path.dirname(self.env.path)
        if 'trac.env_path' in environ:
            del environ['trac.env_path']
        
        req._response = dispatch_request(environ, start_response)
        
    def _send_index(self, req):
        parent_dir = os.path.dirname(self.env.path)
        #env_paths = dict([(filename, os.path.join(parent_dir, filename))
        #                  for filename in os.listdir(parent_dir)])
        projects = []
                          
        for env_name in os.listdir(parent_dir):
            env_path = os.path.join(parent_dir, env_name)
            
            # Don't list this environment
            if env_path == self.env.path:
                continue

            env = None
            try:
                env = _open_environment(env_path)
                #self.log.debug(env.path)
                env_perm = PermissionCache(env, req.authname)
                #self.log.debug(env_perm.perms)
                if env_perm.has_permission('PROJECT_VIEW'):
                    projects.append({
                        'name': env.project_name,
                        'description': env.project_description,
                        'href': req.href.projects(env_name),
                    })
            except Exception, e:
                # Only show errors to admins to prevent excessive disclosure
                if req.perm.has_permission('TRACFORGE_ADMIN'):
                    projects.append({
                        'name': env and env.project_name or env_path,
                        'description': to_unicode(e)
                    })
            
        projects.sort(lambda x, y: cmp(x['name'].lower(), y['name'].lower()))
        req.hdf['tracforge.projects'] = projects
        return 'tracforge_project_index.cs', None
