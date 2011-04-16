# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.web.api import IRequestFilter, ITemplateStreamFilter, IRequestHandler
from genshi.filters.transform import Transformer
from genshi.template import MarkupTemplate
from api import TicketTemplate
from api import LocaleUtil

_TRUE_VALUES = ('true', 'enabled', '1', 1, True)

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
        if template == 'ticket.html':
            add_script(req, 'ticketext/ticketext.js')
            add_stylesheet(req, 'ticketext/ticketext.css')
            
            # localization
            locale = LocaleUtil().get_locale(req)
            if (locale == 'ja'):
                add_script(req, 'ticketext/ticketext-locale-ja.js')
            
        return (template, data, content_type)
    
    
    # ITemplateStreamFilter method
    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'ticket.html':
            return stream
        
        # if specify disable, not execute.
        enable = True
        if 'ticketext' in req.args:
            enable = req.args['ticketext']
            enable = enable.lower() in _TRUE_VALUES
            enable = bool(enable)
        if not enable:
            return stream
        
        readyDescription = False
        if req.path_info == '/newticket' and 'preview' not in req.args:
            readyDescription = True
        
        script = '\n<script type="text/javascript">\n'\
               + 'var tikectTemplate = new ticketext.TicketTemplate(\'' + req.base_path + '\');\n'\
               + 'tikectTemplate.setElementId(\'field-type\', \'field-description\');\n'\
               + 'tikectTemplate.setReadyDescription(' + str(readyDescription).lower() + ');\n'\
               + 'tikectTemplate.initialize();\n'\
               + '</script>\n'
        
        return stream | Transformer('//div[@id="footer"]').before(MarkupTemplate(script).generate())


class TicketTypeChangeHandler(Component):
    implements(IRequestHandler)

    # IRequestHandler method
    def match_request(self, req):
        match = False
        if req.path_info == '/ticketext/template':
            match = True
        else:
            match = False
        
        return match
    
    # IRequestHandler method
    def process_request(self, req):
        template_api = TicketTemplate()
        template_api.process_tickettemplate(self.env, req, 'type')
