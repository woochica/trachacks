# -*- coding: utf-8 -*-
# Copyright (C) 2006 Ashwin Phatak
# Copyright (C) 2007 Dave Gynn
# Copyright (C) 2010 Brian Meeker

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, Chrome, \
                            add_script, add_stylesheet
from genshi.filters.transform import Transformer

__all__ = ['QueryBatchModifyModule']

class QueryBatchModifyModule(Component):
    implements(IPermissionRequestor, ITemplateProvider, ITemplateStreamFilter)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_BATCH_MODIFY'

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
        from pkg_resources import resource_filename
        return [('batchmod', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, formdata):
        """Adds BatchModify form to the query page"""
        if filename == 'query.html' and self._has_permission(req):
            self.log.debug('BatchModifyPlugin: rendering template')
            return stream | Transformer('//div[@id="help"]'). \
                                before(self._generate_query_form(req, formdata) )
        return stream

    def _generate_query_form(self, req, data):
        batchFormData = dict(data)
        batchFormData['query_href']= req.session['query_href'] \
                                     or req.href.query()
        
        add_script(req, 'batchmod/js/query_batchmod.js')
        add_stylesheet(req, 'batchmod/css/batchmod.css')
        stream = Chrome(self.env).render_template(req, 'query_batchmod.html',
              batchFormData, fragment=True)
        return stream.select('//form[@id="batchmod_form"]')
            
    # Helper methods
    def _has_permission(self, req):
        return req.perm.has_permission('TICKET_ADMIN') or \
                req.perm.has_permission('TICKET_BATCH_MODIFY')