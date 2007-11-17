# MacroPost dispatcher
# Copyright 2006 Noah Kantrowitz
from trac.core import *
from trac.mimeview.api import Context
from trac.resource import Resource
from trac.web.api import IRequestFilter
from trac.wiki.formatter import Formatter, WikiProcessor
from trac.wiki.model import WikiPage

from api import IMacroPoster

import re

class MacroPostModule(Component):
    """Magical class that trys to allow macros to POST."""

    macro_posters = ExtensionPoint(IMacroPoster)

    implements(IRequestFilter)
    
    macro_re = re.compile('\[\[(\w+)(?:\([^)]*\))?\]\]')
    proc_re  = re.compile('\{\{\{\n#!(\w+).*?\}\}\}', re.S)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.path_info.startswith('/wiki'):
            if req.method == 'POST' and req.args.get('action','view') == 'view':
                post_handler = None
                for poster in self.macro_posters:
                    if not hasattr(poster, 'match_macro_post'): continue
                    rv = poster.match_macro_post(req)
                    if isinstance(rv, (str, unicode)):
                        rv = rv in req.args.keys()
                    if rv:
                        post_handler = poster
                        break
                if post_handler:
                    post_handler.process_macro_post(req)
                else:
                    # Silly stuff here
                    self.log.debug('MacroPostModule: Unclaimed POST, scanning page %s', req.path_info[6:])
                    page = WikiPage(self.env, req.path_info[6:])
                    matches = self.macro_re.findall(page.text) + self.proc_re.findall(page.text)
                    for name in matches:
                        self.log.debug('MacroPostModule: Found macro "%s"', name)
                        resource = Resource('wiki', name)
                        context = Context.from_request(req, resource)
                        wp = WikiProcessor(Formatter(self.env, context), name)
                        if wp.macro_provider is None:
                            self.log.debug('MacroPostModule: Invalid name!!! How did that happen')
                            continue
                        if hasattr(wp.macro_provider, 'process_macro_post') and \
                           not hasattr(wp.macro_provider, 'match_macro_post'):
                            wp.macro_provider.process_macro_post(req)
                req.environ['REQUEST_METHOD'] = 'GET' # Revert back to a GET

        return handler
        
    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)
