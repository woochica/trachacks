## AMB SearchAll - Search multiple trac projects at once

from trac.core import *
from trac.web.href import Href
try:
    from trac.search import ISearchSource, shorten_result
except ImportError:
    from trac.Search import ISearchSource, shorten_result

try:
    from trac.search.web_ui import SearchModule
except ImportError:
    from trac.Search import SearchModule

from trac.perm import IPermissionRequestor
from trac.env import open_environment
from trac.util import Markup

import re
import posixpath
import os
import logging
import copy


from fnmatch import fnmatch

class SearchAllPlugin(Component):
    """ Search the source repository. """
    implements(ISearchSource)

    # ISearchSource methods
    def get_search_filters(self, req):
        yield ('searchall', 'All projects', 0)

    def get_search_results(self, req, query, filters):
        #return if search all is not active
        if 'searchall' not in filters:
            return

        # get search path and base_url
        search_path, this_project = os.path.split(self.env.path)
        base_url, _ = posixpath.split(req.abs_href())

        #Closes #4158, thanks to jholg
        if 'tracforge' in self.config: 
            if self.config.get('tracforge', 'master_path') == self.env.path: 
                base_url = '/'.join((base_url, this_project, 'projects'))  
            
        # remove 'meta' from filters
        subfilters = [];
        for filter in filters:
           if not filter == 'searchall':
               subfilters.append( filter )      
               
        for project in os.listdir(search_path):
            # skip our own project
            if project == this_project:
                continue
            
            # make up URL for project
            project_url = '/'.join( (base_url, project) )  
            
            project_path = os.path.join(search_path,project)
            if not os.path.isdir( project_path ):
                continue
            
            try:
                env = open_environment(project_path)
            except:
                continue
                        
           
            self.env.log.debug("Searching project %s" % project )
            self.env.log.debug("Searching for %s" % query[0] )           
            self.env.log.debug("Searching with filters %s" % subfilters )

            # don't do anything if we have no filters
            if not subfilters:
                continue
                
            results = []
            env_search = SearchModule(env)
            
            #Update request data
            orig_href = req.href
            req.href = Href(project_url)
            
            for source in env_search.search_sources:
                results += list(source.get_search_results(req, query, subfilters))
            
            req.href = orig_href
            
            for result in results:
                yield (result[0],
                Markup('%s: %s' % (env.project_name, result[1])))\
                + result[2:]
            
