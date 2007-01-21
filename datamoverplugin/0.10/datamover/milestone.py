from trac.core import *
from trac.web.main import _open_environment
from trac.ticket.model import Milestone

from webadmin.web_ui import IAdminPageProvider

from api import DatamoverSystem
from util import copy_milestone

class DatamoverMilestoneModule(Component):
    """The milestone moving component of the datamover plugin."""

    implements(IAdminPageProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('mover', 'Data Mover', 'milestone', 'Milestones')
    
    def process_admin_request(self, req, cat, page, path_info):
        envs = DatamoverSystem(self.env).all_environments()
        milestones = [m.name for m in Milestone.select(self.env)]
        
        if req.method == 'POST':
            source_type = req.args.get('source')
            if not source_type or source_type not in ('milestone', 'all'):
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
            
            milestone_filter = None
            if source_type == 'milestone':
                in_milestones = req.args.getlist('milestone')
                milestone_filter = lambda c: c in in_milestones
            elif source_type == 'all':
                milestone_filter = lambda c: True
            
            try:
                sel_milestones = [m for m in milestones if milestone_filter(m)]
                dest_db = _open_environment(dest).get_db_cnx()
                for milestone in sel_milestones:
                    copy_milestone(self.env, dest, milestone, dest_db)
                dest_db.commit()
                    
                if action == 'move':
                    for milestone in sel_milestones:
                        Milestone(self.env, milestone).delete()
                    
                req.hdf['datamover.message'] = '%s milestones %s'%(action_verb, ', '.join(sel_milestones))
            except TracError, e:
                req.hdf['datamover.message'] = "An error has occured: \n"+str(e)
                self.log.warn(req.hdf['datamover.message'], exc_info=True)
        
        
        req.hdf['datamover.envs'] = envs
        req.hdf['datamover.milestones'] = milestones
        return 'datamover_milestone.cs', None
