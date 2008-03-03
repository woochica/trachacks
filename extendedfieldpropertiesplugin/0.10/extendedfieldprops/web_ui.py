# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2008 McMaster University
#
# This software is licensed under the GPLv2 or later, and a copy is available
# in the COPYING, which you should have received as part of this distribution.
# The terms are also available at
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.html.
#
# Author: Servilio Afre Puentes <afrepues@mcmaster.ca>
 
import pkg_resources

from trac.core import *
from trac.web import IRequestFilter
from trac.web.chrome import ITemplateProvider


class ExtendedTicketCustomizer(Component):
    """Extend ticket stock and custom fields customization options.

    Right now it is restricted to label for stock fields, e.g.:
    
    [ticket]
    ...
    type.label = My type label
    ...

    and skipping (hiding) of custom fields:

    [ticket-custom]
    ...
    customfield.skip = True
    ...

    Right now this only works for the ticket templates, not the report or
    other modules, and custom templates are needed to override the type
    label, if don't need this, the template provider interface can be
    disabled.
    
    """
    
    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter method
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, content_type):
        if req.path_info.startswith('/ticket'):
            place = 'ticket'
        elif req.path_info.startswith('/newticket'):
            place = 'newticket'
        else:
            return (template, content_type)

        config = self.config['ticket']
        for option, value in config.options():
            if '.' not in option:
                continue
            field, prop = option.split('.')
            if field == 'type':
                template = 'efp_' + template
             if prop == 'label':
                req.hdf['%s.fields.%s.label' % (place, field, )] = value
            elif prop == 'skip' and config.getbool(option):
                req.hdf['%s.fields.%s.skip' % (place, field, )] = True

        config = self.config['ticket-custom']
        for option, value in config.options():
            if '.' not in option:
                continue
            field, prop = option.split('.')
            if prop == 'skip' and config.getbool(option):
                req.hdf['%s.fields.%s.skip' % (place, field, )] = True
        
        return (template, content_type)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [pkg_resources.resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []


