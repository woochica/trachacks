from trac.core import *
from trac.web.main import _open_environment
from trac.ticket.model import Component as TicketComponent

from webadmin.web_ui import IAdminPageProvider

from api import DatamoverSystem
from util import copy_component

class DatamoverComponentModule(Component):
    """The ticket component moving component of the datamover plugin."""

    implements(IAdminPageProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('mover', 'Data Mover', 'component', 'Components')
    
    def process_admin_request(self, req, cat, page, path_info):
        envs = DatamoverSystem(self.env).all_environments()
        components = [c.name for c in TicketComponent.select(self.env)]
        
        if req.method == 'POST':
            source_type = req.args.get('source')
            if not source_type or source_type not in ('component', 'all'):
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
            
            comp_filter = None
            if source_type == 'component':
                in_components = req.args.getlist('component')
                comp_filter = lambda c: c in in_components
            elif source_type == 'all':
                comp_filter = lambda c: True
            
            try:
                sel_components = [c for c in components if comp_filter(c)]
                dest_db = _open_environment(dest).get_db_cnx()
                for comp in sel_components:
                    copy_component(self.env, dest, comp, dest_db)
                dest_db.commit()
                    
                if action == 'move':
                    for comp in sel_components:
                        TicketComponent(self.env, comp).delete()
                    
                req.hdf['datamover.message'] = '%s components %s'%(action_verb, ', '.join(sel_components))
            except TracError, e:
                req.hdf['datamover.message'] = "An error has occured: \n"+str(e)
                self.log.warn(req.hdf['datamover.message'], exc_info=True)
        
        
        req.hdf['datamover.envs'] = envs
        req.hdf['datamover.components'] = components
        return 'datamover_component.cs', None
