#Author:   Eoin Dunne
#email:   edunnesoftwaretesting@hotmail.com
#May 2008
#
#
#Thanks to the guys at TRAC and the author of the TRAC admin tool.  The main controller is based on your design.
#
#Long live open source!

import re

import string
import os
import sys, traceback
import time
import logging
import logging.handlers
from trac.core import *
from trac.ticket import Milestone, Ticket, TicketSystem
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet



class ITestManagerRequestHandler(Interface):
    """
    Extension point interface for adding pages to the sprint module.
    """
    def get_path( self, req ):
        """
        """

    def process_testmanager_request(self, req, data=None ):
        """
        """
    def get_descriptive_name(self):
        """
        """
 
class TestManager (Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)
    
    #class variable...a collection of objects that implement the ITestManagerRequestHandler interface.  Makes it's super easty to extend...
    page_providers = ExtensionPoint(ITestManagerRequestHandler)
    
    def __init__(self) :
        #in here we could do stuff.
        pass
        
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'testmanagement'
        
    def get_navigation_items(self, req):
        yield ('mainnav', 'TestManagement',
            html.A('TestManagement', href= req.href.testmanagement()))

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match('/testmanagement*', req.path_info)
        return match 
    
    def process_request(self, req):
        
        
        action = req.args.get('action', 'view')
        pagename = req.args.get('page', 'WikiStart')
        version = req.args.get('version')
        data = { "testcase_page_content" : "select option from above list"  }
        
        if pagename.endswith('/'):
            req.redirect(req.href.wiki(pagename.strip('/')))
               
        pageProvider = self.getPageProvider(req)
        
        page_providers_paths = {}  
        for provider in self.page_providers :
            page_providers_paths[ provider.get_path(req) ] = { 'name': provider.get_descriptive_name(), 'path': req.base_url + "/testmanagement/" + provider.get_path(req) }
    
        data["handlers"] = page_providers_paths
                
        if pageProvider : 
            template, data, content_type = pageProvider.process_testmanager_request( req, data )
            return template, data, content_type
            #return 'testManagement.cs',  content_type #content_type probably = none which is by default rendered as MIME type text/html
        
        
        # This tuple is for Genshi (template_name, data, content_type)
        # Without data the trac layout will not appear.
        return 'main.html', data, None
    
    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs 
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]


    def getPageProvider(self, req):
        """Find the page provider if any"""

        self.env.log.info( "PATH INFO : " + repr( req.path_info ) )
        for provider in self.page_providers:
            self.env.log.info( "Provider name : " + repr(provider) )
            if re.match('/testmanagement/' + provider.get_path(req), req.path_info) :
                self.env.log.info( "found provider : " + repr(provider.get_path(req) ) )
                return provider
        
        return None
