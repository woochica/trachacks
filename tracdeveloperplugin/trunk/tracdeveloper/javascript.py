# Created by Noah Kantrowitz on 2008-02-19.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.web.api import IRequestFilter

class JavascriptDeveloperModule(Component):
    """Developer functionality for JavaScript in Trac."""

    implements(IRequestFilter)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.session.get('developer.js.enable_debug') == '1' and \
           req.path_info == '/chrome/common/js/jquery.js':
            req.args['prefix'] = 'developer'
            req.args['filename'] = 'js/jquery-1.2.1.js'
        return handler
            
    def post_process_request(self, req, template, content_type):
        return template, content_type
