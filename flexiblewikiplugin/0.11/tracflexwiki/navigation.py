# -*- coding: utf-8 -*-

import re
from trac.core import implements
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.api import IRequestFilter
from trac.web.chrome import add_ctxtnav, add_stylesheet, INavigationContributor
from trac.wiki.model import WikiPage
from tracflexwiki.core import TracFlexWikiComponent, TracFlexWikiNode
from tracflexwiki.translation import _

class TracFlexWikiNavigation(TracFlexWikiComponent):
    """Flexible wiki navigation.
    """
    
    implements(IRequestFilter, IRequestHandler, INavigationContributor)
    
    # IRequestFilter methods
    
    def pre_process_request(self, req, handler):
        node = TracFlexWikiNode(self.env, name=req.args.get('page', ''), req=req)
        node.fetch_tree()
        req.args['node'] = node
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if self.is_wiki_realm(req):
            add_stylesheet(req, 'flexwiki/flexwiki.css')
        return template, data, content_type
    
    # INavigationContributor methods
    
    def get_active_navigation_item(self, req):
        return 'newpage'
    
    def get_navigation_items(self, req):
        if 'WIKI_CREATE' in req.perm('wiki'):
            yield('mainnav', 'newpage',\
                html.a(_('New page'),\
                href=req.href.flexwiki(action='new', page=req.args.get('node').navpath)))
            
    # IRequestHandler methods
    
    def match_request(self, req):
        return self.match_request_prefix(req)

    def process_request(self, req):
        """Process request to /struct
        """
        add_stylesheet(req, 'common/css/wiki.css')
        name = req.args.get('page', '')
        if ('create' in req.args):
            parent=req.args.get('parent', '')
            if not WikiPage(self.env, parent).exists:
                parent = ''
            req.redirect(req.href.wiki(name, action='edit', parent=parent, title=req.args.get('title', '')))
        if (req.args.get('action', '') == 'new'):
            data = dict({'node' : req.args.get('node'), '_' : _ })
            return 'wiki_create.html', data, None
