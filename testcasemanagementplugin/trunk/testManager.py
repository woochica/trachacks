#!/usr/bin/env python

import re

import string
import os
import sys, traceback
import time
import logging
import logging.handlers
from trac.core import *
from trac.db import get_column_names
from trac.ticket import Milestone, Ticket, TicketSystem
from trac.web import IRequestHandler
from trac.util import Markup
from trac.web.chrome import INavigationContributor
from trac.web.chrome import add_stylesheet, INavigationContributor, ITemplateProvider
from trac.web.href import Href
from trac.wiki import wiki_to_html

#env: The environment, an instance of the trac.env.Environment class (see trac.env). 
#config: The configuration, an instance of the trac.config.Configuration class (see trac.config). 
#log: The configured logger, see the Python logging API for more information. 

#TRAC_PATH = _find_base_path(sys.modules['trac.core'].__file__, 'trac.core')

def main( argv ) :
    """
    
    """
    print "main"


class ITestManagerRequestHandler(Interface):
    """
    Extension point interface for adding pages to the sprint module.
    """
    def get_path( self, req ):
        """
        """

    def process_testmanager_request(self, req ):
        """
        """
    def get_descriptive_name(self):
        """
        """

class TestManager(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider )
    
    #class variable...a collection of objects that implement the ITestManagerRequestHandler interface.  Makes it's super easty to extend...
    page_providers = ExtensionPoint(ITestManagerRequestHandler)
        
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'testmanagement'
        
    #This is for trac to Add sprint to the tabbed header.
    def get_navigation_items(self, req):
        yield ('mainnav', 'testmanagement', Markup('<a href="%s">TestManagement</a>', self.env.href.testmanagement() + '/' ) )


    # IRequestHandler methods
    #let's figure out if we are the one that should care about this request.
    def match_request(self, req):
        match = re.match('/testmanagement*', req.path_info)
        return match 

    #main entry point into this class.  This is a required method of the IRequestHandler interface, which is part of the trac framework.
    def process_request(self, req):
        
        add_stylesheet(req, 'testmanagement/css/testcase.css')
        pageProvider = self.getPageProvider(req)
        
        page_providers_paths = {}  
        for provider in self.page_providers :
            page_providers_paths[ provider.get_path(req) ] = { 'name': provider.get_descriptive_name(), 'path': provider.get_path(req) }
    
        req.hdf['testcase.page_providers_paths'] = page_providers_paths
        
        if pageProvider : 
            template, content_type = pageProvider.process_testmanager_request( req )
            req.hdf['testcase.page_template'] = template
            return 'testcase.cs',  content_type #content_type probably = none which is by default rendered as MIME type text/html
        else :
            req.hdf['testcase.page_content'] = "select option from above list"  #you could insert a message here if you wanted...
                      
        return 'testcase.cs', None #content_type probably = none which is by default rendered as MIME type text/html
       
    
    def getPageProvider(self, req):
        """Find the page provider if any"""

        for provider in self.page_providers:
            if re.match('/testmanagement/' + provider.get_path(req), req.path_info) :
                self.env.log.debug( "found provider : " + repr(provider.get_path(req) ) )
                return provider
        
        return None
        

    # ITemplateProvider

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('testcase', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

if __name__ == '__main__':
    sys.exit( main( sys.argv ) )