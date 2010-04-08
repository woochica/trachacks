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
from trac.util.datefmt import to_datetime

import re
import posixpath
import os
import logging
import copy


from fnmatch import fnmatch

class SearchAllPlugin(Component):
    """ Search the source repository. """
    implements(ISearchSource)
    implements(IPermissionRequestor)

    def get_project_list(self, req):
        # get search path and base_url
        search_path, this_project = os.path.split(self.env.path)
        base_url, _ = posixpath.split(req.abs_href())

        #Closes #4158, thanks to jholg
        if 'tracforge' in self.config: 
            if self.config.get('tracforge', 'master_path') == self.env.path: 
                base_url = '/'.join((base_url, this_project, 'projects'))  

        projects = []
        for project in os.listdir(search_path):

            # skip our own project
            if project == this_project:
                continue
            
            # make up URL for project
            project_url = '/'.join( (base_url, project) )              
            project_path = os.path.join(search_path, project)
            
            if not os.path.isdir( project_path ):
                continue
            try:
                env = open_environment(project_path, use_cache = True)
            except:
                try:
                    env = open_environment(project_path)
                except:
                    continue
            
            projects.append((project, project_path, project_url, env))
            
        return projects

    # ISearchSource methods
    def get_search_filters(self, req):
        
        if not req.perm.has_permission('SEARCHALL_VIEW') and not req.perm.has_permission('TRAC_ADMIN'):
            return
                
        if hasattr(req, 'is_searchall_recursive'):
            return
            
        req.is_searchall_recursive = True
        
        #Check what filters are available in current project
        existing_filters = []
        env_search = SearchModule(self.env)
        for source in env_search.search_sources:
            if source == self: continue
            existing_filters += source.get_search_filters(req)
        
        #Now get the filters available in other projects
        projects = self.get_project_list(req)
        for project, project_path, project_url, env in projects:
            env_search = SearchModule(env)
            
            available_filters = []
            for source in env_search.search_sources:
                available_filters += source.get_search_filters(req)
        
            for filter in available_filters:
                if filter in existing_filters: continue
                existing_filters.append(filter)
                self.env.log.debug("Yielding %s from project %s", filter, project)
                yield filter
        
        yield ('searchall', 'All projects', 0)

    def get_search_results(self, req, query, filters):
        #return if search all is not active
        if 'searchall' not in filters:
            return
            
        if not req.perm.has_permission('SEARCHALL_VIEW') and not req.perm.has_permission('TRAC_ADMIN'):
            return

        # remove 'searchall' from filters
        subfilters = [];
        for filter in filters:
           if not filter == 'searchall':
               subfilters.append( filter )
        # don't do anything if we have no filters
        if not subfilters:
            return

        projects = self.get_project_list(req)
        
        for project, project_path, project_url, env in projects:

            results = []
            env_search = SearchModule(env)
            
            #available_filters = []
            #for source in env_search.search_sources:
            #    available_filters += source.get_search_filters(req)
            #subfilters = [x[0] for x in available_filters if x[0] != 'searchall']
           
            self.env.log.debug("Searching project %s" % project )
            self.env.log.debug("Searching for %s" % query[0] )           
            self.env.log.debug("Searching with filters %s" % subfilters )

            #Update request data
            orig_href = req.href
            req.href = Href(project_url)
            
            for source in env_search.search_sources:
                for filter in subfilters:
                    try:
                        results += list(source.get_search_results(req, query, [filter]))
                    except Exception, ex:
                        results += [(req.href('search', **req.args), 
                            "<strong>ERROR</strong> in search filter <em>%s</em>" % filter,
                            to_datetime(None), "none", "Exception: %s" % str(ex)),]
            
            req.href = orig_href
            
            for result in results:
                yield (result[0],
                Markup('%s<br/> %s' % (env.project_name, result[1])))\
                + result[2:]
            
    #IPermissionRequestor Methods
    def get_permission_actions(self):
        return ['SEARCHALL_VIEW']