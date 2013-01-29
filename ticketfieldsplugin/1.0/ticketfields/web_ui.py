# -*- coding: utf-8 -*-
"""Trac plugin that adds support for per-ticket custom fields stored in a separate db"""
#
# Copyright (C) 2012 Brian P Hinz
#

from pkg_resources import resource_filename
from genshi.builder import tag
from genshi.filters.transform import Transformer
from trac.core import *
from trac.config import ListOption
from trac.env import IEnvironmentSetupParticipant
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import add_script, add_stylesheet, ITemplateProvider, Chrome
from trac.ticket.api import TicketSystem, ITicketManipulator
from api import TicketTemplates

class TicketFields(Component):
    
    implements(IRequestFilter, ITemplateStreamFilter, ITemplateProvider, IEnvironmentSetupParticipant)

    global_fields = ListOption('ticketfields', 'global_fields', '',
                    """A list of fields that should always be displayed""")
    required_permissions = ['TRAC_ADMIN', 'TICKET_ADMIN', 'TICKET_FIELD_ADMIN']

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        # Check for required custom field
        if 'ticket_fields' not in self.config['ticket-custom']:
            return True

        # Check for required permissions
        if 'ticket_field_admin' not in self.config['extra-permissions']:
            return True

        # Fall through
        return False

    def upgrade_environment(self, db):
        cfg = self.config['ticket-custom']
        if 'ticket_fields' not in cfg:
            cfg.set('ticket_fields', 'text')
            self.config.save()

        perms = self.config['extra-permissions']
        if 'ticket_field_admin' not in perms:
            perms.set('ticket_field_admin', '')
            self.config.save()

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.method != 'POST' or not self.check_permissions(req):
            return handler
        if not req.args.get('path_info'):
            return handler
        for k,v in {'cat_id':'ticket', 'panel_id':'type'}.iteritems():
            if k not in req.args or req.args.get(k) != v:
                return handler
        api = TicketTemplates(self.env)
        type = req.args.get('path_info').strip().encode('utf-8')
        tmpl = api.get_ticket_template(type)
        if 'save' in req.args and req.args.get('save') == 'Save':
            ticket_fields = tmpl and tmpl['fields'] or []
            if req.args.get('field_ticket_fields'):
                sel_ticket_fields = req.args.get('field_ticket_fields')
            if not isinstance(sel_ticket_fields, list):
                sel_ticket_fields = [sel_ticket_fields]
            sel_ticket_fields = [x.strip().encode('utf-8') for x in sel_ticket_fields]
            if sorted(sel_ticket_fields) != ticket_fields:
                if tmpl:
                    tmpl['fields'] = sel_ticket_fields
                    api.update(tmpl)
                else:
                    tmpl = {'name': type, 'fields': sel_ticket_fields}
                    api.insert(tmpl)
        return handler

    def post_process_request(self, req, template, data, content_type):
        # Need to disable network.prefetch-next in firefox to prevent it from pre-fetching
        # the "Next Ticket -->" link.
        if req.get_header("X-Moz") == "prefetch":
            return template, data, content_type
        if template == 'ticket.html':
            add_stylesheet(req, 'ticketfields/css/jquery.dataTables.css')
            add_script(req, 'ticketfields/js/jquery.dataTables.min.js')
            add_script(req, 'ticketfields/js/fnGetCheckedNodes.js')

            ticket = data['ticket']
            custom_fields = [f['name'] for f in TicketSystem(self.env).get_custom_fields()]
            # always display standard trac fields
            displayed_fields = [f['name'] for f in TicketSystem(self.env).get_ticket_fields() if f['name'] not in custom_fields]
            displayed_fields.extend([str(f) for f in self.global_fields])
            ticket_fields_field = [f for f in data['fields'] if f['name'] == 'ticket_fields'][0]
            if ticket_fields_field:
                if req.path_info == '/newticket':
                    api = TicketTemplates(self.env)
                    if req.args.get('type'):
                        tmpl = api.get_ticket_template(req.args.get('type'))
                    else:
                        tmpl = api.get_ticket_template(ticket['type'])
                    if tmpl and tmpl['fields']:
                        tmpl_field_names = [str(f) for f in tmpl['fields'] if str(f) in custom_fields]
                        ticket.values['ticket_fields'] = ','.join(tmpl_field_names)
                ticket_fields_names = (ticket.get_value_or_default('ticket_fields') or '').split(',')
                ticket_fields = [f for f in data['fields'] if f['name'] in ticket_fields_names]
                displayed_fields.extend([f['name'] for f in ticket_fields])
                data['ticket_fields'] = [f['name'] for f in data['fields'] if f['name'] in ticket_fields_names]
                data['available_fields'] = [f for f in TicketSystem(self.env).get_custom_fields() if f['name'] not in self.global_fields]
                data['fields'] = [f for f in data['fields'] if f['name'] in displayed_fields]
                data['ticket_fields_field'] = ticket_fields_field
        elif template == 'admin_enums.html':
            if not self.check_permissions(req) or not req.args.get('path_info'):
                return template, data, content_type
            for k,v in {'cat_id':'ticket', 'panel_id':'type'}.iteritems():
                if k not in req.args or req.args.get(k) != v:
                    return template, data, content_type
            add_stylesheet(req, 'ticketfields/css/jquery.dataTables.css')
            add_script(req, 'ticketfields/js/jquery.dataTables.min.js')
            add_script(req, 'ticketfields/js/fnGetCheckedNodes.js')
            api = TicketTemplates(self.env)
            tmpl = api.get_ticket_template(req.args.get('path_info'))
            data['available_fields'] = [f for f in TicketSystem(self.env).get_custom_fields() if f['name'] not in self.global_fields]
            if tmpl:
                data['ticket_fields'] = [f['name'] for f in data['available_fields'] if f['name'] in tmpl['fields']]
            else:
                data['ticket_fields'] = []
        return template, data, content_type

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if req.get_header("X-Moz") == "prefetch":
            return stream
        if filename == "ticket.html":
            if not self.check_permissions(req):
                return stream
            chrome = Chrome(self.env)
            filter = Transformer('//fieldset[@id="properties"]')
            # add a hidden div to hold the ticket_fields input
            snippet = tag.div(style="display:none;")
            snippet = tag.input(type="hidden", id="field-ticket_fields", name="field_ticket_fields", value=','.join(data['ticket_fields']))
            stream = stream | filter.after(snippet)
            if req.path_info != '/newticket':
                # insert the ticket field groups after the standard trac 'Change Properties' field group
                stream = stream | filter.after(chrome.render_template(req, 'ticket_fields_datatable.html', data, fragment=True))
        elif filename == "admin_enums.html":
            if not self.check_permissions(req) or not req.args.get('path_info'):
                return stream
            for k,v in {'cat_id':'ticket', 'panel_id':'type'}.iteritems():
                if k not in req.args or req.args.get(k) != v:
                    return stream
            if 'ticket_fields' in data:
                chrome = Chrome(self.env)
                filter = Transformer('//div[@class="buttons"]')
                # add a hidden div to hold the ticket_fields input
                snippet = tag.div(style="display:none;")
                snippet = tag.input(type="hidden", id="field-ticket_fields", name="field_ticket_fields", value=','.join(data['ticket_fields']))
                stream = stream | filter.before(snippet)
                stream = stream | filter.before(chrome.render_template(req, 'ticket_fields_datatable.html', data, fragment=True))
        return stream

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('ticketfields', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    # internal methods
    def check_permissions(self, req):
        for required in self.required_permissions:
            if required in req.perm:
                return True
        return False
