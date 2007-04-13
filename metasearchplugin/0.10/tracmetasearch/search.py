## Meta-Search - Search multiple trac projects at once
#
# The tracmetasearch plugin is a first shot at searching multiple trac 
# repositories at a time. 
#
# It performs searches using equal filters and queries on all trac repositories 
# configured for the ProjectMenu Plugin.
#
# tracmetasearch is currently implemented using the XMLRPC Plugin (and python's
# xmlrpc api). 
#
# Both ProjectMenu and XMLRPC plugin must be installed and configured.
# Access to all trac projects must be unrestricted from localhost for the 
# XMLRPC searches to work.
#

from trac.core import *
from trac.web.main import _open_environment
from trac.Search import ISearchSource, shorten_result
from trac.perm import IPermissionRequestor

import re
import posixpath
import os
import logging

import xmlrpclib

from fnmatch import fnmatch

class TracMetaSearchPlugin(Component):
    """ Search the source repository. """
    implements(ISearchSource, IPermissionRequestor)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'META_SEARCH'

    # ISearchSource methods
    def get_search_filters(self, req):
        if req.perm.has_permission('META_SEARCH'):
            yield ('meta', 'All projects', 0)

    def get_search_results(self, req, query, filters):
        # return if we don't do a meta-search
        if 'meta' not in filters:
            return
        # return if meta-searches are not allowed
        if not req.perm.has_permission('META_SEARCH'):
            return

        # get search path and base_url
        search_path, this_project = os.path.split(self.env.path)
        base_url, _ = posixpath.split(req.abs_href())
        
        for project in os.listdir(search_path):
            # skip our own project
            if project == this_project:
                continue
            
            # make up URL for project
            project_url = '/'.join( (base_url, project, 'xmlrpc') )        
            
            # remove 'meta' from filters
            rpc_filters = [];
            for filter in filters:
               if not filter == 'meta':
                   rpc_filters.append( filter )
            
            self.env.log.debug("Searching project %s" % project )
            self.env.log.debug("Searching URL %s" % project_url )
            self.env.log.debug("Searching for %s" % query[0] )           
            self.env.log.debug("Searching with filters %s" % rpc_filters )

            # don't do anything if we have no filters
            if not rpc_filters:
                continue
            
            # try searching remote repositories
            try:
                # the URL is the first component of the project list
                # 
                server = xmlrpclib.ServerProxy( project_url )
            
                # get query results
                results = server.search.performSearch( query[0], rpc_filters );

            except:
                self.env.log.error("Error searching %s " % project_url)
                self.env.log.error("XmlRpcPlugin installed and configured? http(s) access allowed? XML_RPC privilege granted?")
                continue

            # return on empty query results
            if not results:
                continue
            
            for result in results:
                # result is a list containing
                # (href, title, date, author, excerpt)
                yield result
