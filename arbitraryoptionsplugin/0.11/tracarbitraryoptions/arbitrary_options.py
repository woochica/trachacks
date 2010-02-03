# Copyright (c) 2009-2010 David Isaacson
# Copyright (c) 2003-2008 Edgewall Software
# All rights reserved
#
# This software is licensed under the modified BSD License.
# See the included file 'LICENSE' for more information.

from trac.core import Component, implements
from trac.env import open_environment
from trac.web.main import get_environments
from trac.web.api import IRequestFilter, RequestDone
from trac.util.text import to_unicode

class ArbitraryOptionsPlugin(Component):
    implements(IRequestFilter)

    #magic self variables: env, config, log
    
    def __init__(self):
        self.env.project_info = dict(self.config.options('project_info'))
            
    #IRequestFilter
    """Extension point interface for components that want to filter HTTP
    requests, before and/or after they are processed by the main handler."""
    
    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
       
        Always returns the request handler, even if unchanged.
        """
        return handler

    # for ClearSilver templates
    def post_process_request(self, req, template, content_type):
        """Do any post-processing the request might need; typically adding
        values to req.hdf, or changing template or mime type.
       
        Always returns a tuple of (template, content_type), even if
        unchanged.

        Note that `template`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (for 0.10 compatibility; only used together with ClearSilver templates)
        """
        return (template, content_type)

    # for Genshi templates
    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
       
        `data` may be update in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (Since 0.11)
        """
             
        try:
            data['project_info'] = self.env.project_info
        except TypeError, err:
           self.log.error(str(data['project_info']))

        try:
           _get_project_index(req, data)
        except TypeError, err:
           self.log.error(err)
        
        return (template, data, content_type)


# Modified from trac's web.main.send_project_index
def _get_project_index(req, data):

    environ = req.environ

    try:
        #href = Href(req.base_path)
        projects = []
        for env_name, env_path in get_environments(environ).items():
            try:
                env = open_environment(env_path, use_cache=not environ['wsgi.run_once'])
                proj = {
                    'name': env.project_name,
                    'description': env.project_description,
                    'href': env_name,
                    'info': env.project_info
                }
            except Exception, e:
                proj = {'name': env_name, 'description': to_unicode(e), 'info': {}}
            projects.append(proj)

        projects.sort(lambda x, y: cmp(x['name'].lower(), y['name'].lower()))

        data['projects'] = projects

    except RequestDone:
        pass
