# -*- coding: utf-8 -*-
# Copyright (C) 2008 Abbywinters.com
# trac-dev@abbywinters.com
# Contributor: Zach Miller

import re
from datetime import datetime 
from trac.core import *
from trac.perm import IPermissionRequestor        
from trac.ticket import TicketSystem, Ticket
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.main import IRequestHandler
from trac.util.datefmt import utc
from trac.ticket.notification import TicketNotifyEmail
from genshi.filters.transform import Transformer
from genshi.builder import tag

__all__ = ['GridModifyModule']

class GridModifyModule(Component):
    implements(IPermissionRequestor, IRequestHandler, ITemplateProvider, ITemplateStreamFilter)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_GRID_MODIFY'

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('gridmod', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return []
    
    # IRequestHandler methods
    def match_request(self, req):
        """Handle requests to /trac/gridmod URLs"""
        return re.match(r'/gridmod(?:/.*)?$', req.path_info)

    def process_request(self, req):
        """Process AJAX request from select controls on modified query and report pages."""
        try:
            if(req.perm.has_permission('TICKET_ADMIN') or req.perm.has_permission('TICKET_GRID_MODIFY')):            
                now = datetime.now(utc)
                id = req.args.get('ticket')
                ticket = Ticket(self.env, id)
                for field in TicketSystem(self.env).get_ticket_fields():
                    val = req.args.get(field['name'])
                    if(field['type'] == 'select' and ((val in field['options']) or (val == ''))):
                        ticket[field['name']] = val;
                ticket.save_changes(author=req.authname, comment='updated by gridmod plugin')
                tn = TicketNotifyEmail(self.env)
                tn.notify(ticket, newticket=False, modtime=now)
                # Add support for workflow actions
            else:
                raise Exception('Permission denied')
        except Exception, e:
            req.send_response(500)
            req.send_header('Content-Type', 'text/plain')
            req.end_headers()
            req.write("Oops...\n");
            import traceback;
            req.write(traceback.format_exc()+"\n");
        else:
            req.send_response(200)
            req.send_header('Content-Type', 'text/plain')
            req.end_headers()
            req.write('OK')
            

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, formdata):
        """Modifies query page to add selectors"""
        if (filename == 'query.html' or filename == 'report_view.html') and (req.perm.has_permission('TICKET_ADMIN') or req.perm.has_permission('TICKET_GRID_MODIFY')):
            add_script(req, 'gridmod/gridmod.js')
            for field in TicketSystem(self.env).get_ticket_fields():
                if field['type'] == 'select':
                    xpath = '//*[contains(@class, "tickets")]//td[contains(@class, "%s")]' % (field['name'])
                    select = tag.select(name=field['name'])
                    # HACK: For some reason custom fields that have a blank value
                    # as a valid option don't actually have that blank
                    # value among the options in field['options'] so
                    # we force a blank option in in the case where the
                    # _default_ value is blank.
                    if(field.has_key('value') and field['value'] == '' and not ('' in field['options'])):
                        select.append(tag.option())
                    for option in field['options']:
                        select.append(tag.option(option, value=option))
                    stream |= Transformer(xpath).wrap(tag.td(class_=field['name'])).rename('div').attr('class', 'gridmod_default').attr('style', 'display: none').before(tag.form(select, class_='gridmod_form'))
        return stream
    


