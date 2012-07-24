# -*- coding: utf8 -*-

import pkg_resources

from trac.core import *
from trac.web import ITemplateStreamFilter
from trac.web.chrome import add_script, add_stylesheet, ITemplateProvider

class DuplicateTicketSearch(Component):
    implements(ITemplateProvider, ITemplateStreamFilter)

    # ITemplateProvider methods
        
    def get_htdocs_dirs(self):
        return [('duplicateticketsearch', pkg_resources.resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


    # ITemplateStreamFilter methods
    
    def filter_stream(self, req, method, filename, stream, data):
    
        if filename == 'ticket.html':
            ticket = data.get('ticket')
            if ticket and not ticket.id:   # only add for new tickets
                add_script(req, 'duplicateticketsearch/js/tracDupeSearch.js')                
                add_stylesheet(req, 'duplicateticketsearch/css/tracDupeSearch.css')
            
        return stream

