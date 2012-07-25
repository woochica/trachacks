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
        if len(path) < 2 or path[0] != 'attachment' or req.args.get('action') == 'delete':
            return handler

        if not path[-1].lower().endswith('.pdf'):
            return handler

        filename = req.href(*(['raw-attachment'] + path[1:]))

        req.redirect(filename) 





