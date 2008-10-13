# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.web.api import IRequestFilter, ITemplateStreamFilter, IRequestHandler
from genshi.filters.transform import Transformer
from genshi.template import MarkupTemplate
from api import TicketTemplate

class TicketTemplateModule(Component):
    implements(ITemplateProvider, IRequestFilter, ITemplateStreamFilter)

    # ITemplateProvider method
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ticketext', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider method
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # IRequestFilter method
    def pre_process_request(self, req, handler):
        return handler
    
    # IRequestFilter method
    def post_process_request(self, req, template, content_type):
        return (template, content_type)

    # IRequestFilter method
    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html' and req.path_info == '/newticket':
            add_script(req, 'ticketext/ticketext.js')
            add_stylesheet(req, 'ticketext/ticketext.css')
            
        return (template, data, content_type)
    
    
    # ITemplateStreamFilter method
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html' and req.path_info == '/newticket':
            script = '\n<script type="text/javascript">'\
                   + 'TicketTemplate.initialize(\'field-type\', \'field-description\');'\
                   + '</script>\n'
            return stream | Transformer('//div[@id="footer"]').before(MarkupTemplate(script).generate())
        
        return stream


class TicketTypeChangeHandler(Component):
    implements(IRequestHandler)

    # IRequestHandler method
    def match_request(self, req):
        if req.path_info == '/ticketext/template':
            return True
        else:
            return False
    
    # IRequestHandler method
    def process_request(self, req):
        template_api = TicketTemplate(self.env)
        template_api.process_tickettemplate(req, 'type')
