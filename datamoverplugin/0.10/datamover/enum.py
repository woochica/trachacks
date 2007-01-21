from trac.core import *
from trac.web.main import _open_environment

from webadmin.web_ui import IAdminPageProvider

from api import DatamoverSystem
from util import copy_enum

class DatamoverEnumModule(Component):
    """The ticket enum moving component of the datamover plugin."""

    implements(IAdminPageProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('mover', 'Data Mover', 'enum', 'Enums')
    
    def process_admin_request(self, req, cat, page, path_info):
        envs = DatamoverSystem(self.env).all_environments()
        source_db = self.env.get_db_cnx()
        source_cursor = source_db.cursor()
        source_cursor.execute('SELECT type, name FROM enum')
        hashed_enums = {}
        for enum_type, enum_name in source_cursor:
            hashed_enums.setdefault(enum_type, []).append(enum_name)
        
        if req.method == 'POST':
            source_type = req.args.get('source')
            if not source_type or source_type not in ('type', 'enum', 'all'):
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
            
            enum_filter = None
            if source_type == 'type':
                sel_type = req.args.get('enumtype')
                enum_filter = lambda e: e[0] == sel_type
            elif source_type == 'enum':
                sel_enums = [(k,v) for k,v in req.args.items() if k.startswith('enum[')]
                enum_filter = lambda e: ('enum[%s]' % e[0], e[1]) in sel_enums
            elif source_type == 'all':
                enum_filter = lambda c: True
            
            try:
                filtered_enums = [e for e in enums if enum_filter(e)]
                dest_db = _open_environment(dest).get_db_cnx()
                for enum in filtered_enums:
                    copy_enum(self.env, dest, enum[0], enum[1], dest_db)
                dest_db.commit()
                    
                if action == 'move':
                    for enum in filtered_enums:
                        source_cursor.execute('DELETE FROM enum WHERE type=%s AND name=%s', enum)
                    
                req.hdf['datamover.message'] = '%s enums %s'%(action_verb, ', '.join(['%s:%s'%e for e in filtered_enums]))
            except TracError, e:
                req.hdf['datamover.message'] = "An error has occured: \n"+str(e)
                self.log.warn(req.hdf['datamover.message'], exc_info=True)
        
        
        req.hdf['datamover.envs'] = envs
        for k in hashed_enums:
            req.hdf['datamover.enums.' + k] = hashed_enums[k]
        req.hdf['datamover.enumtypes'] = hashed_enums.keys()
        return 'datamover_enum.cs', None
