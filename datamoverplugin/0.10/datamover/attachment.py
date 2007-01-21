from trac.core import *
from trac.web.main import _open_environment
from trac.attachment import Attachment
from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage

from webadmin.web_ui import IAdminPageProvider

from api import DatamoverSystem
from util import copy_attachment

try:
    set = set
except NameError:
    from sets import Set as set

class DatamoverAttachmentModule(Component):
    """The attachment moving component of the datamover plugin."""

    implements(IAdminPageProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('mover', 'Data Mover', 'attachment', 'Attachments')
    
    def process_admin_request(self, req, cat, page, path_info):
        envs = DatamoverSystem(self.env).all_environments()
        source_db = self.env.get_db_cnx()
        source_cursor = source_db.cursor()
        source_cursor.execute("SELECT id FROM attachment WHERE type = 'wiki'")
        wiki_pages = list(set([a for (a,) in source_cursor])) # kill duplicates
        wiki_pages.sort()
        
        if req.method == 'POST':
            source_type = req.args.get('source')
            if not source_type or source_type not in ('type', 'wiki', 'ticket', 'all'):
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
            
            att_filter = None
            if source_type == 'type':
                in_type = req.args.get('type')
                att_filter = lambda a: a.parent_type == in_type
            elif source_type == 'wiki':
                in_pages = req.args.getlist('wiki')
                att_filter = lambda a: a.parent_type == 'wiki' and a.parent_id in in_pages
            elif source_type == 'ticket':
                in_ticket = req.args.get('ticket')
                att_filter = lambda a: a.parent_type == 'ticket' and a.parent_id == in_ticket
            elif source_type == 'all':
                att_filter = lambda c: True
            
            try:
                source_cursor.execute('SELECT type,id,filename FROM attachment')
                attachments = [Attachment(self.env,t,i,f) for (t,i,f) in source_cursor]
                sel_attachments = [a for a in attachments if att_filter(a)]
                dest_db = _open_environment(dest).get_db_cnx()
                for att in sel_attachments:
                    copy_attachment(self.env, dest, att.parent_type, att.parent_id, att.filename, dest_db)
                dest_db.commit()
                    
                if action == 'move':
                    for att in sel_attachments:
                        att.delete()
                    
                req.hdf['datamover.message'] = '%s attachments %s'%(action_verb, ', '.join(["%s:%s" % (a.parent_id, a.filename) for a in sel_attachments]))
            except TracError, e:
                req.hdf['datamover.message'] = "An error has occured: \n"+str(e)
                self.log.warn(req.hdf['datamover.message'], exc_info=True)
        
        
        req.hdf['datamover.envs'] = envs
        req.hdf['datamover.wiki_pages'] = wiki_pages
        return 'datamover_attachment.cs', None
