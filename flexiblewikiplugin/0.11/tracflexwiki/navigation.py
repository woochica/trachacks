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
        #self.env.log.debug("FLEX pre_process_request")
        self._get_node(req)
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if self.is_wiki_realm(req):
            add_stylesheet(req, 'flexwiki/flexwiki.css')
        return template, data, content_type
   
    def _get_node(self, req):
        #self.env.log.debug("FLEX Getting node...")
        if 'node' not in req.args:
            node = TracFlexWikiNode(self.env, name=req.args.get('page', ''), req=req)
            node.fetch_tree()
            req.args['node'] = node
        return req.args.get('node')

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'newpage'
    
    def get_navigation_items(self, req):
        #self.env.log.debug("FLEX get_navigation_items")
        node = self._get_node(req)
        if 'WIKI_CREATE' in req.perm('wiki'):
            yield('mainnav', 'newpage',\
                html.a(_('New page'),\
                href=req.href.flexwiki(action='new', page=node.navpath)))
            
    # IRequestHandler methods
    
    def match_request(self, req):
        return self.match_request_prefix(req)

    def process_request(self, req):
        """Process request to /struct
        """
        add_stylesheet(req, 'common/css/wiki.css')
        name = req.args.get('page', '')
        node = self._get_node(req)
        if ('create' in req.args):
            parent=req.args.get('parent', '')
            if not WikiPage(self.env, parent).exists:
                parent = ''
            req.redirect(req.href.wiki(name, action='edit', parent=parent, title=req.args.get('title', '')))
        if (req.args.get('action', '') == 'new'):
            data = dict({'node' : node, '_' : _ })
            return 'wiki_create.html', data, None
