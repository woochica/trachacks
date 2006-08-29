from trac.core import *
from trac.env import Environment
from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage

from webadmin.web_ui import IAdminPageProvider

from api import DatamoverSystem
from util import copy_wiki_page

import fnmatch, re

# TODO: datamover.ticket and datamover.wiki should really be in the same module

class DatamoverWikiModule(Component):
    """The wiki page moving component of the datamover plugin."""

    implements(IAdminPageProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('WIKI_ADMIN'):
            yield ('mover', 'Data Mover', 'wiki', 'Wiki')
    
    def process_admin_request(self, req, cat, page, path_info):
        envs = DatamoverSystem(self.env).all_environments()
        
        if req.method == 'POST':
            source_type = req.args.get('source')
            if not source_type or source_type not in ('prefix', 'glob', 'regex'):
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
            
            page_filter = None
            if source_type == 'prefix':
                page_filter = lambda p: p.startswith(source.strip())
            elif source_type == 'glob':
                page_filter = lambda p: fnmatch.fnmatch(p, source)
            elif source_type == 'regex':
                page_filter = lambda p: re.search(re.compile(source, re.U), p)
                
                            
            try:
                pages = [p for p in WikiSystem(self.env).get_pages() if page_filter(p)]
                dest_db = Environment(dest).get_db_cnx()
                for page in pages:
                    copy_wiki_page(self.env, dest, page, dest_db)
                dest_db.commit()
                    
                if action == 'move':
                    for id in ids:
                        WikiPage(self.env, page).delete()
                    
                req.hdf['datamover.message'] = '%s pages %s'%(action_verb, ', '.join(pages))
            except TracError, e:
                req.hdf['datamover.message'] = "An error has occured: \n"+str(e)
                self.log.warn(req.hdf['datamover.message'], exc_info=True)
            


        req.hdf['datamover.envs'] = envs
        return 'datamover_wiki.cs', None


