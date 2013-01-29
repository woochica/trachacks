# -*- coding: utf-8 -*-
"""Trac plugin that adds support for grouping ticket fields"""
#
# Copyright (C) 2012 Brian P Hinz
#

from genshi.input import HTML
from genshi.builder import tag
from genshi.template import *
from genshi.template.loader import *
from genshi.template.plugin import *
from genshi.filters.transform import Transformer
from operator import itemgetter,attrgetter
from pkg_resources import resource_filename

from trac.core import *
from trac.config import Option, IntOption, BoolOption, ListOption
from trac.ticket.api import TicketSystem, ITicketManipulator
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import add_script, add_script_data, add_stylesheet, ITemplateProvider, Chrome

from api import FieldGroups

class FieldGroupsModule(Component):
    
    implements(IRequestFilter, ITemplateStreamFilter, ITemplateProvider)
    
    default_class = Option('fieldgroups', 'default_class', '', doc="Default CSS class to apply")
    #template_name = Option('fieldgroups', 'template_name', '', doc="Default CSS class to apply")
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        # Need to disable network.prefetch-next in firefox to prevent it from pre-fetching
        # the "Next Ticket -->" link.
        if req.get_header("X-Moz") == "prefetch":
            return template, data, content_type
        if template == 'ticket.html':
            ticket = data['ticket']
            api = FieldGroups(self.env)
            data['field_groups'] = []
            for g in api.get_field_groups():
                g['fields'] = [f for f in data['fields'] if f['name'] in g['fields'] and not f['skip']]
                if g['fields']:
                    data['field_groups'].append(g)
                    for f in g['fields']:
                        f['skip'] = True
            add_stylesheet(req, 'fieldgroups/css/fieldgroups_ticket.css')
            add_stylesheet(req, 'fieldgroups/css/fieldgroups_ticket_box.css')
        return template, data, content_type

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == "ticket.html" and req.get_header("X-Moz") != "prefetch":
            chrome = Chrome(self.env)
            # append the ticket fields to the end of the standard trac ticket box
            filter = Transformer('//div[@id="ticket"]')
            stream = stream | filter.append(chrome.render_template(req, 'fieldgroups_ticket_box.html', data, fragment=True))
            # insert the ticket field groups after the standard trac 'Change Properties' field group
            filter = Transformer('//fieldset[@id="properties"]')
            stream = stream | filter.after(chrome.render_template(req, 'fieldgroups_properties.html', data, fragment=True))
            #filter = Transformer('//fieldset[@id="action"]')
            #stream = stream | filter.before(chrome.render_template(req, 'fieldgroups_properties.html', data, fragment=True))
        return stream

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('fieldgroups', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

