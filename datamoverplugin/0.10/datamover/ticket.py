from trac.core import *
from trac.env import Environment
from trac.ticket.model import Component as TicketComponent, Ticket
from trac.ticket.query import Query

from webadmin.web_ui import IAdminPageProvider

from api import DatamoverSystem
from ticket_util import copy_ticket

class DatamoverTicketModule(Component):
    """The ticket moving component of the datamover plugin."""

    implements(IAdminPageProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            yield ('mover', 'Data Mover', 'ticket', 'Ticket')
    
    def process_admin_request(self, req, cat, page, path_info):
        components = [c.name for c in TicketComponent.select(self.env)]
        envs = DatamoverSystem(self.env).all_environments()
        
        if req.method == 'POST':
            source_type = req.args.get('source')
            if not source_type or source_type not in ('component', 'ticket'):
                raise TracError, "Source type not specified or invalid"
            source = req.args.get(source_type)
            dest = req.args.get('destination')
            action = None
            if 'copy' in req.args.keys():
                action = 'copy'
            elif 'move' in req.args.keys():
                action = 'move'
            else:
                raise TracError, 'Action not specified or invalid'
                
            action_verb = {'copy':'Copied', 'move':'Moved'}[action]
            
            query_string = {
                'ticket': 'id=%s'%int(source),
                'component': 'component=%s'%source,
                'all': 'id!=0',
                'query': source,
            }
                
            try:
                ids = [x['id'] for x in Query.from_string(self.env, query_string).execute(req)]
                dest_db = Environment(dest).get_db_cnx()
                for id in ids:
                    copy_ticket(self.env, dest, id, dest_db)
                dest_db.commit()
                    
                if action == 'move':
                    for id in ids:
                        Ticket(self.env, id).delete()
                    
                req.hdf['datamover.message'] = '%s tickets %s'%(action_verb, ', '.join([str(n) for n in ids]))
            except TracError, e:
                req.hdf['datamover.message'] = "An error has occured: \n"+str(e)
                self.log.warn(req.hdf['datamover.message'], exc_info=True)
            


        req.hdf['datamover.components'] = components
        req.hdf['datamover.envs'] = envs
        return 'datamover_ticket.cs', None


