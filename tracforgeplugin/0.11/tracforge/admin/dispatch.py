# Created by Noah Kantrowitz on 2007-04-09.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
import sys
import inspect
import os
import os.path
import copy
import traceback

from trac.core import *
from trac.core import ComponentMeta
from trac.env import open_environment
from trac.web.api import IRequestHandler, Request, Cookie
from trac.web.main import dispatch_request, RequestDispatcher, RequestDone
from trac.web.chrome import INavigationContributor
from trac.perm import PermissionCache
from trac.util.text import to_unicode
from trac.web.href import Href
from trac.mimeview.api import Mimeview

from genshi.builder import tag

class TracForgeIndexModule(Component):
    """A request handler to show a nicer project index."""
    
    implements(IRequestHandler, INavigationContributor)

    def match_request(self, req):
        return req.path_info == '/projects'

    def process_request(self, req):
        data = {}
        req.perm.require('PROJECT_LIST')
    
        parent_dir = os.path.dirname(self.env.path)
        #env_paths = dict([(filename, os.path.join(parent_dir, filename))
        #                  for filename in os.listdir(parent_dir)])
        projects = []
                          
        for env_name in os.listdir(parent_dir):
            env_path = os.path.join(parent_dir, env_name)
            
            # Don't list this environment
            if env_path == self.env.path:
                continue
            
            # Only bother looking at folders
            if not os.path.isdir(env_path):
                continue
            
            try:
                env = open_environment(env_path, use_cache=True)

                try:
                    self.log.debug('TracForge: %s', env.path)
                    env_perm = PermissionCache(env, req.authname)
                    #self.log.debug(env_perm.perms)
                    if 'PROJECT_VIEW' in env_perm:
                        projects.append({
                            'name': env.project_name,
                            'description': env.project_description,
                            'href': req.href.projects(env_name),
                        })
                except Exception, e:
                    # Only show errors to admins to prevent excessive disclosure
                    if 'TRACFORFGE_ADMIN' in req.perm:
                        projects.append({
                            'name': env.project_name,
                            'description': e
                        })
            except Exception, e:
                if 'TRACFORGE_ADMIN' in req.perm:
                    projects.append({
                        'name': env_path,
                        'description': e,
                    })
        
        data['projects'] = projects
        return 'tracforge_project_list.html', data, None
        
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'projects'

    def get_navigation_items(self, req):
        if 'PROJECT_LIST' in req.perm:
            yield 'mainnav', 'projects', tag.a('Projects', href=req.href.projects())
            

class TracForgeDispatcherModule(Component):
    """A request handler to dispatch /projects as if it were a TRAC_ENV_PARENT_DIR folder."""

    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request(self, req):
        if req.path_info.startswith('/projects'):
            path_info = req.path_info[10:]
            if path_info:
                self.log.debug('TracForgeDispatch: Starting WSGI relaunch for %s (%s)', path_info, req.method)
                project = path_info.split('/', 1)[0]
                # Check that we aren't trying to recurse (possible link loop)
                if project == os.path.basename(self.env.path):
                    req.redirect(req.href())
                    
                # Assert permissions on the desination environment
                try:
                    project_env = open_environment(os.path.join(os.path.dirname(self.env.path), project), use_cache=True)
                except IOError:
                    raise TracError('No such project "%s"'%project)
                
                # Check that we have permissions in the desired project
                authname = RequestDispatcher(self.env).authenticate(req)
                project_perm = PermissionCache(project_env, authname)
                project_perm.require('PROJECT_LIST')
                
                start_response = req._start_response
                environ = copy.copy(req.environ)
                
                # Setup the environment variables
                environ['SCRIPT_NAME'] = req.href.projects('/')
                environ['PATH_INFO'] = path_info
                environ['trac.env_parent_dir'] = os.path.dirname(self.env.path)
                if 'TRAC_ENV' in environ:
                    del environ['TRAC_ENV']
                if 'trac.env_path' in environ:
                    del environ['trac.env_path']
                environ['tracforge_master_link'] = req.href.projects()

                # Remove mod_python options to avoid conflicts
                if 'mod_python.subprocess_env' in environ:
                    del environ['mod_python.subprocess_env']
                if 'mod_python.options' in environ:
                    del environ['mod_python.options']

                req._response = dispatch_request(environ, start_response)
                raise RequestDone

    def process_request(self, req):
        raise TracError('How did I get here?')

