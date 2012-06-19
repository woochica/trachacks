# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering
#

from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import add_script, add_script_data, add_stylesheet, ITemplateProvider
from genshi.builder import tag
from genshi.filters.transform import Transformer
from pkg_resources import resource_filename

class GroupTicketFields(Component):
    
    implements(IRequestFilter, ITemplateStreamFilter, ITemplateProvider)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            fields = data.get('fields')
            filtered_fields = []
            append_fields = []
            remove_fields = []
            groups = []
            group_order = []
            
            options = self.config.options('group-ticket-fields')

            for option in self.config.options('group-ticket-fields'):
                if option[0] == 'group_order':
                    group_order = self.config.getlist('group-ticket-fields', 'group_order')
                elif option[0].find('.') == -1:
                    group = { 'name' : option[0], 'label': option[1] }

                    if self.config.has_option('group-ticket-fields', '%s.fields' % option[0]):
                        group['fields'] = self.config.getlist('group-ticket-fields', '%s.fields' % option[0])

                    if self.config.has_option('group-ticket-fields', '%s.properties' % option[0]):
                        group['properties'] = self.config.getlist('group-ticket-fields', '%s.properties' % option[0])

                    if self.config.has_option('group-ticket-fields', '%s.columns' % option[0]):
                        group['columns'] = self.config.getint('group-ticket-fields', '%s.columns' % option[0])

                    groups.append(group)

                    remove_fields.extend(group['fields'])

            for field in data.get('fields'):
                if field['name'] not in remove_fields:
                    filtered_fields.append(field)
                else:
                    append_fields.append(field)

            filtered_fields.extend(append_fields)

            groups_list = { 'field_groups': groups }
            group_order = { 'field_groups_order': group_order }
            data['fields'] = filtered_fields
            data['field_groups'] = groups
            
            add_script_data(req, groups_list)
            add_script_data(req, group_order)
            add_script(req, 'groupticketfields/group_ticket_fields.js')
            add_stylesheet(req, 'groupticketfields/css/ticket.css')

        return template, data, content_type
        
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == "ticket.html":
            filter = Transformer('//fieldset[@id="properties"]')

            field_groups = data.get('field_groups')
            for group in field_groups:
                stream = stream | filter.after(self._field_group(req, group))

        return stream

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('groupticketfields', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        # return [resource_filename(__name__, 'templates')]
        return []

    # Internal
    def _field_group(self, req, group):
        fieldset_id = 'properties_%s' % group['name']
        table_id = 'table_%s' % group['name']

        fieldset = tag.fieldset(id=fieldset_id, class_='property_group')
        fieldset.append(tag.legend(group['label']))
        fieldset.append(tag.table(id=table_id))

        return fieldset
