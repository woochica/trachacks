# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from trac import ticket
from trac.admin import IAdminPanelProvider
from trac.config import BoolOption, ListOption
from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.web.chrome import ITemplateProvider

from customfieldadmin.api import CustomFields


class CondFieldsAdmin(Component):
    implements(ITemplateProvider, IAdminPanelProvider)

    include_std = BoolOption('condfields', 'include_standard', default='true',
                             doc='Include the standard fields for all types.')
    show_default = BoolOption('condfields', 'show_default', default='false',
                              doc='Default is to show or hide selected fields.')
    forced_fields = ListOption('condfields', 'forced_fields', doc='Fields that cannot be disabled',
                               default="type, summary, reporter, description, status, resolution, priority")

    def __init__(self):
        # Initialize ListOption()s for each type.
        # This makes sure they are visible in IniAdmin, etc
        self.types = [t.name for t in ticket.Type.select(self.env)]
        for t in self.types:
            setattr(self.__class__, '%s_fields' % t,
                    ListOption('condfields', t,
                               doc='Fields to include for type "%s"' % t))

    ### ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    ### IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('ticket', 'Ticket System', 'typecondfields', 'Ticket Type Fields')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TRAC_ADMIN')

        if req.method == 'POST':
            self._process_update(req)

        page_param = {}
        self._process_read(req, page_param)

        return "condfields_admin.html", {'template': page_param}

    def _process_read(self, req, page_param):
        ticket_type = req.args.get('type')

        ticket_types = [{
            'name': type.name,
            'value': type.value,
            'selected': (type.name == ticket_type),
            'hidden': ','.join(set(getattr(self, type.name + '_fields')))
        } for type in ticket.Type.select(self.env)]

        if ticket_type is None:
            ticket_type = (ticket_types[0])['name']

        custom_fields_api = CustomFields(self.env)
        page_param['types'] = ticket_types
        standard_fields = []
        custom_fields = []
        for f in TicketSystem(self.env).get_ticket_fields():
            if f.get('custom'):
                custom_fields.append(f)
            else:
                standard_fields.append(f)
        custom_fields = [f for f in custom_fields if f['name'] not in self.forced_fields]
        standard_fields = [f for f in standard_fields if f['name'] not in self.forced_fields]
        page_param['customfields'] = custom_fields
        page_param['standardfields'] = standard_fields
        page_param['forcedfields'] = self.forced_fields

    def _process_update(self, req):
        ticket_type = req.args.get('type')
        ticket_hide = req.args.get('cf-hide')

        ticket_hide_fields = ''
        if ticket_hide is not None:
            if isinstance(ticket_hide, list):
                ticket_hide_fields = ','.join(ticket_hide)
            else:
                ticket_hide_fields = ticket_hide

        # set the configuration now
        self.config.set('condfields', ticket_type, ticket_hide_fields)
        self.config.save()
