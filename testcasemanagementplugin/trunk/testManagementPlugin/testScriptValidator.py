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
        #for now let's just re-direct to a query page that shows all open testcases grouped by owner and ordered by milestone 
        #query_URL = req.base_url + "/query?status=new&status=assigned&status=reopened&testcase_result=&type=testcase&order=milestone&group=owner"
        #req.redirect( query_URL )
        tempTestCaseList = []
        
        projTemplates = self.properties.getTemplates(self, req )
        for name in projTemplates.getTemplateNames() : 
            name = name.encode('ascii', 'ignore')
            testIds = projTemplates.getTestsForTemplate( name )
            if testIds != None : 
                for id in testIds : 
                    if id not in tempTestCaseList :
                        tempTestCaseList.append( id )
            
            
        allTestcases, errors = self.properties.getTestCases( self, req ) #fetch the testcases...
        
        if allTestcases == None : 
            return False, None
        
        for testId in tempTestCaseList:
            if testId in allTestcases : 
                continue
            else:
                errors.append( "The test: " + testId + ", in the testtemplates.xml file cannont be matched with a real test case" )
                       
        if errors : 
            req.hdf['testcase.run.errormessage'] = errors
            return "testRunNotConfigured.cs", None
        else:
            return "validated.cs", None

    def get_path( self, req ):
        return "validate"
        
    def get_descriptive_name(self):
        return "Validate Test Scripts"

        


#env: The environment, an instance of the trac.env.Environment class (see trac.env). 
#config: The configuration, an instance of the trac.config.Configuration class (see trac.config). 
#log: The configured logger, see the Python logging API for more information. 
