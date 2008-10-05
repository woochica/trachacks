# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.web.api import IRequestFilter, IRequestHandler
from trac.util.html import Markup
from api import TicketTemplate

class TicketTemplateProvider(Component):
    implements(ITemplateProvider)

    # ITemplateProvider method
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ticketext', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider method
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


class TicketTemplateFilter(Component):
    implements(IRequestFilter)

    # IRequestFilter method
    def pre_process_request(self, req, handler):
        return handler

    # IRequestFilter method
    def post_process_request(self, req, template, content_type):
        if template == 'newticket.cs':
            add_script(req, 'ticketext/jquery.js')
            add_script(req, 'ticketext/ticketext.js')
            add_stylesheet(req, 'ticketext/ticketext.css')
            footer = req.hdf['project.footer'] + '\n<script type="text/javascript">'\
                                               + 'TicketTemplate.initialize(\'type\', \'description\');'\
                                               + '</script>\n'
            req.hdf['project.footer'] = Markup(footer)
            
        return (template, content_type)


class TicketTypeChangeHandler(Component):
    implements(IRequestHandler)

    # IRequestHandler method
    def match_request(self, req):
        if req.path_info == '/ticketExtTemplate':
            return True
        else:
            return False
    
    # IRequestHandler method
    def process_request(self, req):
        template_api = TicketTemplate(self.env)
        template_api.process_tickettemplate(req, 'type')
