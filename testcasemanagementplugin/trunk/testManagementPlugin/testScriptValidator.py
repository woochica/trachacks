#!/usr/bin/env python

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
   

class TestScriptValidator(Component):
    implements(ITestManagerRequestHandler)
    
    properties = Properties() #get set up with with a properties instance...
        
    def process_testmanager_request(self, req ):
        #check for errors in the testcases and configuration, if there are no errors let the user know, and vice versa
        try:
            errors = self.properties.validateTestCases( self, req )
            
            if errors : 
                req.hdf['testcase.run.errormessage'] = errors
                return "testRunNotConfigured.cs", None
            else:
                req.hdf['testcase.validate.pathConfiguration'] = self.properties.getTestCasePath( self, req)
                req.hdf['testcase.validate.urlPath'] = req.base_url + "/testmanagement/runs?pathConfiguration=" + self.properties.getTestCasePath( self, req) 
                return "validated.cs", None
        except Exception, ex:
            req.hdf['testcase.run.errormessage'] = str( ex )
            return "testRunNotConfigured.cs", None
            
    def get_path( self, req ):
        return "validate"
        
    def get_descriptive_name(self):
        return "Validate Test Scripts from mainline"

        


#env: The environment, an instance of the trac.env.Environment class (see trac.env). 
#config: The configuration, an instance of the trac.config.Configuration class (see trac.config). 
#log: The configured logger, see the Python logging API for more information. 
