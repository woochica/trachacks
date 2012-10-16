# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.web.api import IRequestFilter

class PDFRedirector(Component):

    implements(IRequestFilter)

    ### IRequestFilter methods

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    def pre_process_request(self, req, handler):

        path = req.path_info.strip('/').split('/')

        if len(path) > 1 and path[-1].lower().endswith('.pdf'):
            if path[0] == 'attachment' and not req.args.get('action') == 'delete':
                filepath = req.href(*(['raw-attachment'] + path[1:]))
                req.redirect(filepath)
            elif path[0] == 'browser':
                path[0] = 'export'
                rev = req.args.get('rev', 'HEAD')
                path.insert(1, rev)
                filepath = req.href('/'.join(path))
                req.redirect(filepath)

        return handler
