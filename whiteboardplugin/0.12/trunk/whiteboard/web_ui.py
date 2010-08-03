# -*- coding: utf-8 -*-
# Copyright (C) 2010 Brian Meeker
from pkg_resources import resource_filename
from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script, \
                              add_stylesheet, add_ctxtnav

class WhiteboardModule(Component):
    
    implements(ITemplateProvider, ITemplateStreamFilter)
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)
    
        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
    
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return [('whiteboard', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
    
    # IRequestFilter methods
    def filter_stream(self, req, method, filename, stream, formdata):
        if filename == 'query.html':
            add_script(req, 'whiteboard/js/whiteboard.js')
            add_stylesheet(req, 'whiteboard/css/whiteboard.css')
            add_ctxtnav(req, "Whiteboard", "#")
        return stream