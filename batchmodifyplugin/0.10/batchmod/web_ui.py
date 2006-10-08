# -*- coding: utf-8 -*-
# Copyright (C) 2006 Ashwin Phatak

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor        
from trac.ticket.query import QueryModule
from trac.util.html import html
from trac.ticket import TicketSystem
from trac.ticket import Ticket

__all__ = ['BatchModifyModule']

class BatchModifyModule(Component):
    '''Allows batch modification of tickets'''

    implements(INavigationContributor, IRequestHandler, ITemplateProvider, \
                IPermissionRequestor)
    
    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return "query"

    def get_navigation_items(self, req):
        from trac.ticket.report import ReportModule
        if req.perm.has_permission('TICKET_VIEW') and \
                not self.env.is_component_enabled(ReportModule):
            yield ('mainnav', 'tickets',
                   html.A('View Tickets', href=req.href.query()))
        yield ('mainnav', 'query',
                   html.A('Custom Query', href=req.href.query()))


    # IRequestHandler methods

    def match_request(self, req):
       return QueryModule(self.env).match_request(req)
    
    def process_request(self, req):
        if req.args.has_key('batchmod'):
            req.perm.assert_permission('TICKET_BATCH_MODIFY')
            self._batch_modify(req)

        QueryModule(self.env).process_request(req)
        self._add_ticket_fields(req)
     
        return 'batchmod.cs', None


    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
   
 
    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_BATCH_MODIFY'


    # Internal methods 
    def _batch_modify(self, req):
        tickets = req.session['query_tickets'].split(' ')
        comment = req.args.get('comment', '') 
        values = {} 
        
        for field in TicketSystem(self.env).get_ticket_fields():
            name = field['name']
            if name not in ('summary', 'reporter', \
                        'description', 'type', 'status',
                        'resolution', 'owner'):
                if req.args.has_key('bm_' + name):
                    values[name] = req.args.get(name)

        for id in tickets:
            t = Ticket(self.env, id) 
            t.populate(values)
            t.save_changes(req.authname, comment)



    def _add_ticket_fields(self, req):   
        for field in TicketSystem(self.env).get_ticket_fields():
            name = field['name']
            del field['name']
            if name in ('summary', 'reporter', 'description', 'type', 'status',
                        'resolution', 'owner'):
                field['skip'] = True
            req.hdf['ticket.fields.' + name] = field


