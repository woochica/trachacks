# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Max Stewart
# All rights reserved.
#
# This file is part of the TicketValidator plugin for Trac
#
# TicketValidator is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as 
# published by the Free Software Foundation, either version 3 of 
# the License, or (at your option) any later version.
#
# TicketValidator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TicketValidator.  If not, see 
# <http://www.gnu.org/licenses/>.

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider

class TicketValidatorAdminPanelProvider(Component):
    """Provides an admin page for modifying validator settings."""
     
    implements(IAdminPanelProvider, ITemplateProvider)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            yield ('ticket', _('Ticket System'), 'validation', _('Ticket Validation'))

    def render_admin_panel(self, req, category, page, path_info):
        
        if req.method == 'POST':
            
            if 'apply' not in req.args:
                return self._handle_add_remove(req, category, page, path_info)
            
            self._update_config(req)
        
        rules = []
        options = self.config.options('ticketvalidator')
        
        for name, value in options:
            req_idx = name.find('.required') 
            if req_idx != -1:
                rules.append({'name': name[0:req_idx], 'fields': value})
        
        return self._render(req, rules)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # Private methods
    def _get_rules(self, req):
        """Get the list of rules from the request.
        
        :param:req the request
        :type:req Request
        :return: a list containing validator rules"""
        
        tmp = {}
        to_remove = []
        
        for name in req.args:
            key, pn = self._splitname(name)
        
            if key not in ('name', 'fields', 'remove'):
                continue
        
            if key == 'remove':
                to_remove.append(pn)
            else:
                if pn not in tmp:
                    tmp[pn] = {}
            
                tmp[pn].update({key: req.args[name]})

        rules = []
        
        for key in tmp:
            if key not in to_remove and tmp[key]['name'] != '':
                rules.append(tmp[key])
                
        return rules

    def _handle_add_remove(self, req, category, page, path_info):
        return self._render(req, self._get_rules(req))

    def _splitname(self, name):
        
        if name.find('_') == -1:
            return name, None
        
        s = name.split('_')
        
        return s[0], s[1]

    def _render(self, req, rules):
        """Render the page."""
        
        rules.append({'': ''})
        
        return 'validator_admin.html', {'rules': rules}
    
    def _update_config(self, req):
        """Save changes to main configuration file."""
        
        for option in self.config['ticketvalidator']:
            self.config.remove('ticketvalidator', option)
        
        rules = self._get_rules(req)
        
        for rule in rules:
            self.config.set('ticketvalidator', rule['name'] + '.required', rule['fields'])
            
        self.config.save()

