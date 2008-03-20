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
                    project_env = _open_environment(os.path.join(os.path.dirname(self.env.path), project))
                except IOError:
                    raise TracError('No such project "%s"'%project)
               
                authname = RequestDispatcher(self.env).authenticate(req)
                project_perm = PermissionCache(project_env, authname)
                project_perm.assert_permission('PROJECT_VIEW')
                self.debug('TracForgeDispath: Access granted, running relaunch')
                self.debug('TracForgeDispatch: Status of req.args is %r', req.__dict__.get('args', 'NOT FOUND'))
                self._send_project(req, path_info)
                self.debug('TracForgeDispatch: Relaunch completed, terminating request')
                self.debug('TracForgeDispatch: Response was %r', req._response)
                
                req._tf_print = True
                
                return True

    def process_request(self, req):
        raise TracError('How did I get here?')

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
                self.log('TracForgeDispatch: start_response called with (%s)', ', '.join(repr(x) for x in args))
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
        
        
        self.debug('TracForgeDispatch: environ %r', environ)
        self.debug('TracForgeDispatch: Calling next dispatch_request')
        try:
            if not hasattr(start_response, 'log'):
                self.debug('TracForgeDispatch: Setting start_request logging hack')
                #start_response = hacked_start_response(start_response, self.log)
            req._response = dispatch_request(environ, start_response)
        except RequestDone:
            self.debug('TracForgeDispatch: Masking inner RequestDone')
        self.debug('TracForgeDispatch: Done')
        
    def _evil_phase_1(self):
        self.debug('TracForgeDispatch: Sending early_error')
        raise Exception # Dump into early_error mode
    anonymous_request = property(_evil_phase_1)

    def _evil_phase_2(self):
        for frame in inspect.stack()[1:]:
            locals = frame[0].f_locals
            if 'early_error' in locals:
                self.debug('TracForgeDispatch: Erasing early_error')
                locals['early_error'][:] = []
                break
        else:
            self.log.error('TracForgeDispatch: evil_phase_2 unable to isolate early error. Contact coderanger ASAP!')
            raise TracError('Something went wrong, check the log and contact coderanger')
        self.debug('TracForgeDispatch: Sending evil RequestDone')
        raise RequestDone
    use_template = property(_evil_phase_2)

    def debug(self, *args):
        # self.log.debug(*args)
        pass

# Evil
# env = None
# for frame in inspect.stack()[1:]:
#     locals = frame[0].f_locals
#     if locals.get('env'):
#         env = locals['env']
#         break

# Make sure we are first
#ComponentMeta._registry[IRequestHandler].remove(TracForgeDispatcherModule)
#ComponentMeta._registry[IRequestHandler].insert(0, TracForgeDispatcherModule)

# Monkey patch Request to lazily evaluate req.args
def __init__(self, environ, start_response):
    self.environ = environ
    self._start_response = start_response
    self._write = None
    self._status = '200 OK'
    self._response = None

    self._inheaders = [(name[5:].replace('_', '-').lower(), value)
                       for name, value in environ.items()
                       if name.startswith('HTTP_')]
    if 'CONTENT_LENGTH' in environ:
        self._inheaders.append(('content-length',
                                environ['CONTENT_LENGTH']))
    if 'CONTENT_TYPE' in environ:
        self._inheaders.append(('content-type', environ['CONTENT_TYPE']))
    self._outheaders = []
    self._outcharset = None

    self.incookie = Cookie()
    cookie = self.get_header('Cookie')
    if cookie:
        self.incookie.load(cookie, ignore_parse_errors=True)
    self.outcookie = Cookie()

    self.base_url = self.environ.get('trac.base_url')
    if not self.base_url:
        self.base_url = self._reconstruct_url()
    self.href = Href(self.base_path)
    self.abs_href = Href(self.base_url)
 
    self._args = None
    #env.log.debug('TracForgeEvil: Using patched init (%s)', id(self))
    
#Request.__init__ = __init__

def get_args(req):
    if not req._args:
        #env.log.debug('TracForgeEvil: Expanding req.args (%s)', id(req))
        #env.log.debug('TracForgeEvil: %s', traceback.format_stack())
        req._args = req._parse_args()
    return req._args

#Request.args = property(lambda self: get_args(self))

# Monkey patch sys.exc_info
exc_info = sys.exc_info
def new_exc_info():
    rv = exc_info()
    if isinstance(rv, tuple):
        rv = list(rv)
    return rv
#sys.exc_info = new_exc_info
