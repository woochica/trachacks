import re

import string
import os
import sys, traceback
import time
import logging
import logging.handlers
from trac.core import *
from trac.ticket import Component as TracComponent, Milestone, Ticket, TicketSystem 
from testManagementPlugin.properties import Properties

from testManager import ITestManagerRequestHandler

#env: The environment, an instance of the trac.env.Environment class (see trac.env). 
#config: The configuration, an instance of the trac.config.Configuration class (see trac.config). 
#log: The configured logger, see the Python logging API for more information. 
   

class SetPathManager (Component):
    implements(ITestManagerRequestHandler)
    
    properties = Properties() #get set up with with a properties instance...
        
    def process_testmanager_request(self, req ):
        if req.method == "POST":

            allTestcases, errors = self.properties.getTestCases( self, req ) #fetch the testcases...
            
            if errors :
                req.hdf['testcase.run.errormessage'] = errors
                return "testRunNotConfigured.cs", None      
            else : 
                 req.redirect( req.base_url + "/testmanagement/runs?pathConfiguration=" + self.properties.getTestCasePath( self, req) )

        else:
            req.hdf['testcases.path.path'] = self.properties.getTestCasePath( self, req)
            return "choosePathForTestRun.cs", None

    def get_path( self, req ):
        return "testrunbranch"
        
    def get_descriptive_name(self):
        return "Create Test Run from branch or tag location"

        


#env: The environment, an instance of the trac.env.Environment class (see trac.env). 
#config: The configuration, an instance of the trac.config.Configuration class (see trac.config). 
#log: The configured logger, see the Python logging API for more information. 