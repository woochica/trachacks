from trac.core import *
from trac.web.main import _open_environment
from trac.ticket.model import Version

from webadmin.web_ui import IAdminPageProvider

from api import DatamoverSystem
from util import copy_version

class DatamoverVersionModule(Component):
    """The version moving component of the datamover plugin."""

    implements(IAdminPageProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('mover', 'Data Mover', 'version', 'Versions')
    
    def process_admin_request(self, req, cat, page, path_info):
        envs = DatamoverSystem(self.env).all_environments()
        versions = [v.name for v in Version.select(self.env)]
        
        if req.method == 'POST':
            source_type = req.args.get('source')
            if not source_type or source_type not in ('version', 'all'):
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
            
            ver_filter = None
            if source_type == 'version':
                in_versions = req.args.getlist('version')
                ver_filter = lambda c: c in in_versions
            elif source_type == 'all':
                ver_filter = lambda c: True
            
            try:
                sel_versions = [v for v in versions if ver_filter(v)]
                dest_db = _open_environment(dest).get_db_cnx()
                for version in sel_versions:
                    copy_version(self.env, dest, version, dest_db)
                dest_db.commit()
                    
                if action == 'move':
                    for version in sel_versions:
                        Version(self.env, version).delete()
                    
                req.hdf['datamover.message'] = '%s versions %s'%(action_verb, ', '.join(sel_versions))
            except TracError, e:
                req.hdf['datamover.message'] = "An error has occured: \n"+str(e)
                self.log.warn(req.hdf['datamover.message'], exc_info=True)
        
        
        req.hdf['datamover.envs'] = envs
        req.hdf['datamover.versions'] = versions
        return 'datamover_version.cs', None
