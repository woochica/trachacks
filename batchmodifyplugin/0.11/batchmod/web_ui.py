# -*- coding: utf-8 -*-
# Copyright (C) 2006 Ashwin Phatak
# Copyright (C) 2007 Dave Gynn

from trac.core import *
from trac.perm import IPermissionRequestor        
from trac.ticket import TicketSystem, Ticket
from trac.ticket.query import QueryModule
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, Chrome
from trac.web.main import IRequestFilter
from genshi.filters.transform import Transformer

__all__ = ['BatchModifyModule']

class BatchModifyModule(Component):
    implements(IPermissionRequestor, ITemplateProvider, IRequestFilter, ITemplateStreamFilter)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_BATCH_MODIFY'

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        """Look for QueryHandler posts and hijack them"""
        if req.path_info == '/query' and req.method=='POST' and \
            req.args.get('batchmod') and self._has_permission(req):
            self.log.debug('BatchModifyModule: executing')
            self._batch_modify(req)
        return handler

    def post_process_request(self, req, template, content_type):
        """No-op"""
        return (template, content_type)

    def post_process_request(self, req, template, data, content_type):
        """No-op"""
        return (template, data, content_type)
    
    # Internal methods 
    def _batch_modify(self, req):
        tickets = req.session['query_tickets'].split(' ')
        comment = req.args.get('bmod_value_comment', '') 
        values = {} 

        # TODO: improve validation and better handle advanced statuses
        for field in TicketSystem(self.env).get_ticket_fields():
            name = field['name']
            if name not in ('summary', 'reporter', 'description'):
                if req.args.has_key('bmod_flag_' + name):
                    values[name] = req.args.get('bmod_value_' + name)

        selectedTickets = req.args.get('selectedTickets')
        self.log.debug('BatchModifyPlugin: selected tickets: %s', selectedTickets)
        selectedTickets = isinstance(selectedTickets, list) and selectedTickets or selectedTickets.split(',')
        if not selectedTickets:
            raise TracError, 'No Tickets selected'
        
        for id in selectedTickets:
            if id in tickets:
                t = Ticket(self.env, id) 
                t.populate(values)
                t.save_changes(req.authname, comment)
                self.log.debug('BatchModifyPlugin: saved changes to #%s', id)

                # TODO: Send email notifications - copied from ticket.web_ui
                #try:
                #    tn = TicketNotifyEmail(self.env)
                #    tn.notify(ticket, newticket=False, modtime=now)
                #except Exception, e:
                #    self.log.exception("Failure sending notification on change to "
                #                       "ticket #%s: %s" % (ticket.id, e))
    
                # TODO: deal with actions and side effects - copied from ticket.web_ui
                #for controller in self._get_action_controllers(req, ticket,
                #                                               action):
                #    controller.apply_action_side_effects(req, ticket, action)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, formdata):
        """Adds BatchModify form to the query page"""
        if filename == 'query.html' and self._has_permission(req):
            return stream | Transformer('//div[@id="help"]'). \
                                before(self._generate_form(req, formdata) )
        return stream

    
    def _generate_form(self, req, data):
        batchFormData = dict(data)
        batchFormData['actionUri']= req.session['query_href'] or req.href.query()

        fields = []
        for field in TicketSystem(self.env).get_ticket_fields():
            if field['name'] not in ('summary', 'reporter', 'description'):
                fields.append(field)
        batchFormData['fields']=fields

        stream = Chrome(self.env).render_template(req, 'batchmod.html',
              batchFormData, fragment=True)
        return stream.select('//form[@id="batchmod-form"]')
        
    # Helper methods
    def _has_permission(self, req):
        return req.perm.has_permission('TICKET_ADMIN') or \
                req.perm.has_permission('TICKET_BATCH_MODIFY')
