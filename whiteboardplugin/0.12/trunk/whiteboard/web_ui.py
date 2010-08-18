# -*- coding: utf-8 -*-
# Copyright (C) 2010 Brian Meeker
from pkg_resources import resource_filename
from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script, \
                              add_stylesheet, add_ctxtnav, Chrome
from genshi.filters.transform import Transformer

__all__ = ['WhiteboardModule']

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
        return [resource_filename(__name__, 'templates')]
    
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, formdata):
        # Don't check for req.path_info == '/query'. This will cause an infinite
        # loop. I think it is matching when the actual QueryModule component then.
        if filename == 'query.html':
            self.log.debug("WhiteboardPlugin: rendering template")
            add_script(req, 'whiteboard/js/whiteboard.js')
            add_script(req, 'whiteboard/js/jquery.equalheights.js')
            add_stylesheet(req, 'whiteboard/css/whiteboard.css')
            add_ctxtnav(req, "Whiteboard", "/#whiteboard")
            
            whiteboard_stream = Chrome(self.env).render_template(req, 
                'whiteboard.html', formdata, fragment=True)
            return stream | Transformer('//div[@id="help"]'). \
                before(whiteboard_stream.select('//div[@id="whiteboard"]'))
        return stream