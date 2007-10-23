# Created by Noah Kantrowitz on 2007-04-09.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
import sys
import inspect
import traceback

from trac.core import *
from trac.core import ComponentMeta
from trac.web.api import IRequestHandler, Request, Cookie
from trac.web.main import dispatch_request, RequestDispatcher, RequestDone

# Compatibility hack to make this code work with older 0.11 revisions
try:
    from trac.env import open_environment as _open_environment
    def open_environment(x): return _open_environment(x,True)
except:
    from trac.web.main import _open_environment as open_environment
    
from trac.web.chrome import INavigationContributor
from trac.perm import PermissionCache
from trac.util.text import to_unicode
from trac.web.href import Href
from trac.util.html import html as tag

import os
import os.path
import copy

class TracForgeIndexModule(Component):
    """A request handler to show a nicer project index."""
    
    implements(IRequestHandler, INavigationContributor)

    def match_request(self, req):
        return req.path_info == '/projects'

    def process_request(self, req):
        parent_dir = os.path.dirname(self.env.path)
        #env_paths = dict([(filename, os.path.join(parent_dir, filename))
        #                  for filename in os.listdir(parent_dir)])
        projects = []
                          
        for env_name in os.listdir(parent_dir):
            env_path = os.path.join(parent_dir, env_name)
            
            # Don't list this environment
            if env_path == self.env.path:
                continue
            
            try:
                env = open_environment(env_path)

                try:
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
                            'name': env.project_name,
                            'description': to_unicode(e)
                        })
            except Exception, e:
                if req.perm.has_permission('TRACFORGE_ADMIN'):
                    projects.append({
                        'name': env_path,
                        'description': to_unicode(e),
                    })
            
        projects.sort(lambda x, y: cmp(x['name'].lower(), y['name'].lower()))
        req.hdf['tracforge.projects'] = projects
        return 'tracforge_project_index.cs', None
        
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'projects'

    def get_navigation_items(self, req):
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
                    project_env = open_environment(os.path.join(os.path.dirname(self.env.path), project))
                except IOError:
                    raise TracError('No such project "%s"'%project)
               
                authname = RequestDispatcher(self.env).authenticate(req)
                project_perm = PermissionCache(project_env, authname)
                project_perm.assert_permission('PROJECT_VIEW')
                self.log.debug('TracForgeDispath: Access granted, running relaunch')
                self.log.debug('TracForgeDispatch: Status of req.args is %r', req.__dict__.get('args', 'NOT FOUND'))
                #self.log.debug('TracForgeDispatch: wsgi.input contains %s', req.read())
                self._send_project(req, path_info)
                self.log.debug('TracForgeDispatch: Relaunch completed, terminating request')
                self.log.debug('TracForgeDispatch: Response was %r', req._response)
                
                req._tf_print = True
                
                raise RequestDone, 'request done'

    def process_request(self, req):
        raise TracError('How did I get here?')
        path_info = req.path_info[10:]
        
        if path_info:
            project = path_info.split('/', 1)[0]
            
            # Check that we aren't trying to recurse (possible link loop)
            if project == os.path.basename(self.env.path):
                req.redirect(req.href())
                
            # Assert permissions on the desination environment
            project_path = os.path.join(os.path.dirname(self.env.path), project)
            try:
                project_env = open_environment(project_path)
            except IOError:
                raise TracError('No such project "%s" at %s'% (project,project_path))
            project_perm = PermissionCache(project_env, req.authname)
            project_perm.assert_permission('PROJECT_VIEW')
            
            return self._send_project(req, path_info)
        else:
            return self._send_index(req)
            
    # Internal methods
    def _send_project(self, req, path_info):
        start_response = req._start_response
        environ = copy.copy(req.environ)
        
        class hacked_start_response(object):
        
            def __init__(self, start_response, log):
                if hasattr(start_response, 'log'):
                    raise Exception("BOOM!")
                self.start_response = start_response
                self.log = log
                
            def __call__(self, *args):
                self.log.debug('TracForgeDispatch: start_response called with (%s)', ', '.join(repr(x) for x in args))
                return self.start_response(*args)
        
        environ['SCRIPT_NAME'] = req.href.projects('/')
        environ['PATH_INFO'] = path_info
        environ['trac.env_parent_dir'] = os.path.dirname(self.env.path)
        if 'TRAC_ENV' in environ:
            del environ['TRAC_ENV']
        if 'trac.env_path' in environ:
            del environ['trac.env_path']
        environ['tracforge_master_link'] = req.href.projects()
        
        # Remove mod_python option to avoid conflicts
        if 'mod_python.subprocess_env' in environ:
            del environ['mod_python.subprocess_env']
        if 'mod_python.options' in environ:
            del environ['mod_python.options']
        
        
        self.log.debug('TracForgeDispatch: environ %r', environ)
        self.log.debug('TracForgeDispatch: Calling next dispatch_request')
        try:
            if not hasattr(start_response, 'log'):
                self.log.debug('TracForgeDispatch: Setting start_request logging hack')
                #start_response = hacked_start_response(start_response, self.log)
            req._response = dispatch_request(environ, start_response)
        except RequestDone:
            self.log.debug('TracForgeDispatch: Masking inner RequestDone')
        self.log.debug('TracForgeDispatch: Done')
        
# Make sure we are first
ComponentMeta._registry[IRequestHandler].remove(TracForgeDispatcherModule)
ComponentMeta._registry[IRequestHandler].insert(0, TracForgeDispatcherModule)
