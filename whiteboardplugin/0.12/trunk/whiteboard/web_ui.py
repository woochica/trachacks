# -*- coding: utf-8 -*-
# Copyright (C) 2010 Brian Meeker
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
from pkg_resources import resource_filename
from trac.core import *
from trac.db.api import with_transaction
from trac.ticket import Ticket
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script, \
                              add_stylesheet, add_ctxtnav, Chrome
from trac.web.main import IRequestFilter
from genshi.filters.transform import Transformer

__all__ = ['WhiteboardModule']

class WhiteboardModule(Component):
    
    implements(ITemplateProvider, ITemplateStreamFilter, IRequestFilter)
    
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
        # Don't check for req.path_info == '/query'. This will cause an
        # infinite loop. I think it is matching the actual QueryModule 
        # component then.
        if filename == 'query.html':
            self.log.debug("WhiteboardPlugin: rendering template")
            add_script(req, 'whiteboard/js/whiteboard.js')
            add_script(req, 'whiteboard/js/jquery.equalheights.js')
            add_script(req, 'whiteboard/js/jquery-ui.js')
            add_stylesheet(req, 'whiteboard/css/whiteboard.css')
            add_ctxtnav(req, "Whiteboard", "/#whiteboard")
            
            formdata['query_href']= req.session['query_href'] \
                                     or req.href.query()
            
            whiteboard_stream = Chrome(self.env).render_template(req, 
                'whiteboard.html', formdata, fragment=True)
            return stream | Transformer('//h2[@class="report-result"]..'). \
                before(whiteboard_stream.select('//form[@id="whiteboard_form"]'))
        return stream
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        """Look for QueryHandler posts from the whiteboard form."""
        if req.path_info == '/query' and req.method=='POST' and \
            req.args.get('whiteboard_submit'):
            self.log.debug('WhiteboardModule: request.args=%s', req.args)
            self._process_request(req)
            req.redirect(req.args.get('query_href'))
        return handler


    def post_process_request(self, req, template, content_type):
        """No-op"""
        return (template, content_type)

    def post_process_request(self, req, template, data, content_type):
        """No-op"""
        return (template, data, content_type)
    
    def _process_request(self, req):
        field = req.args.get('whiteboard_group_by')
        changes = req.args.get('whiteboard_changes')
        
        self.log.debug('WhiteboardModule: field=%s', field)
        self.log.debug('WhiteboardModule: changes=%s', changes)
        
        @with_transaction(self.env)
        def _implementation(db):
            """Apply each change to the ticket and save it."""
            for change in changes.strip(',').split(','):
                change_items = change.split(':')
                self.log.debug('WhiteboardModule: change_items=%s', change_items)
                t = Ticket(self.env, int(change_items[0]))
                values = {}
                values[field] = change_items[1]
                
                t.populate(values)
                t.save_changes(req.authname)