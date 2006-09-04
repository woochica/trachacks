from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.web.api import IRequestFilter
from trac.web.session import Session
from trac.config import IntOption
from trac.ticket.query import QueryModule

import math

class PageQueryModule(Component):
    
    tickets_per_page = IntOption('ticket', 'default_per_page', default=10,
                                 doc="The number of tickets shown per page in queries")
    
    implements(ITemplateProvider, IRequestFilter)
    
    # IRequestFilter
    def pre_process_request(self, req, handler):
        if isinstance(handler, QueryModule):
            if req.method == 'POST':
                # Don't ask, severe evil
                def my_redirect(path):
                    req.session['tickets_perpage'] = req.args.get('per_page')
                    req.real_redirect(path)
                req.real_redirect = req.redirect
                req.redirect = my_redirect
        return handler
        
    def post_process_request(self, req, template, content_type):
        if template == 'query.cs':
        
            # Extract the results from the HDF
            def walk_hdf(node):
                ret = {}
                while node:
                    if node.child():
                        ret[node.name()] = walk_hdf(node.child())
                    else:
                        ret[node.name()] = node.value()
                    node = node.next()
                return ret                
            results_dict = walk_hdf(req.hdf.getObj('query.results').child())
            results = [results_dict[k] for k in sorted(results_dict.keys())]

            # Update/retrieve the number of tickets per page
            perpage = req.session.get('tickets_perpage')
            if not perpage:
                perpage = self.tickets_per_page
            else:
                perpage = int(perpage)

            # Calculate number of pages and current page
            numpages = int(math.ceil(len(results) * 1.0 / perpage))
            curpage = int(req.args.get('page', 1))
            if curpage <= 0 or curpage > numpages:
                raise TracError, 'Invalid page %s'%(curpage)
                
            # Calculate the start and end point
            start = perpage * (curpage-1)
            end = start + perpage
    
            # Reinsert the smaller results set
            req.hdf.removeTree('query.results')        
            req.hdf['query.results'] = results[start:end]
            
            # NOTE: On second thought, the column headers should go back to page 1 anyway
            #def walk_hdf2(node):
            #    while node:
            #        req.hdf['query.headers.%s.href'%node.name()] = req.hdf['query.headers.%s.href'%node.name()] + '&amp;page=%s'%curpage
            #        node = node.next()       
            #walk_hdf2(req.hdf.getObj('query.headers').child())
            
            # A few more HDF variables
            req.hdf['page_query.perpage'] = perpage
            req.hdf['page_query.numpages'] = range(1, numpages+1)
            req.hdf['page_query.curpage'] = curpage
            
            return 'paged_query.cs', content_type
            
       
        return template, content_type

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        return []
