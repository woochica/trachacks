from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script, add_script_data, add_stylesheet
from trac.ticket.api import ITicketManipulator
from trac.config import Option, IntOption, BoolOption, ListOption

from genshi.builder import tag
from genshi.filters.transform import Transformer

import time
from traceback import format_exc
import re

class MultiSelectFieldModule(Component):
    """A trac plugin implementing a custom ticket field that can hold multiple predefined values."""

    implements(IRequestFilter, ITemplateStreamFilter, ITemplateProvider)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, data, content_type):
        mine = ['/newticket', '/ticket', '/simpleticket']

        match = False
        for target in mine:
            if req.path_info.startswith(target):
                match = True
                break

        if match:
            add_script(req, 'multiselectfield/chosen.jquery.min.js')
            add_script(req, 'multiselectfield/multiselectfield.js')
            add_stylesheet(req, 'multiselectfield/chosen.css')
        return template, data, content_type

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):

        if filename == 'ticket.html':
            for field in list(self._multi_select_fields()):

                options = self.config.get('ticket-custom', field + '.options').split('|')
                options_html = tag()
                for option in options:
                    options_html(tag.option(option))

                stream = stream | Transformer('//input[@name="field_' + field + '"]'
                ).attr(
                    'style', 'display:none;'
                ).after(
                    tag.select(multiple="multiple", class_="multiselect", style="width:200px;")(options_html)
                )

        return stream

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('multiselectfield', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        return []

    # Internal methods
    def _multi_select_fields(self):
        for key, value in self.config['ticket-custom'].options():
            if key.endswith('.multiselect') and value == "true":
                yield key.split('.', 1)[0]

