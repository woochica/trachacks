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
import trac.util.text as TracText
from trac.core import *
from trac.ticket import Component as TracComponent, Milestone, Ticket, TicketSystem 
from testManagementPlugin.properties import Properties

from testManager import ITestManagerRequestHandler

#env: The environment, an instance of the trac.env.Environment class (see trac.env). 
#config: The configuration, an instance of the trac.config.Configuration class (see trac.config). 
#log: The configured logger, see the Python logging API for more information. 


class TestRunManager(Component):
    implements(ITestManagerRequestHandler)
    
    #    This class creates sets of tickets based on 4 kinds of inputs...
    #    1. version
    #    2. milestone
    #    3. selected users
    #    4. selected testcases
        
    #    What is a test run?  A test run is a set of testcases for a particular version, milestone and user(s).  The "master" test cases are stored in subversion.
    #    The properties class accesses subversion and provides a list of testcases based on the xml files stored at a particular place as specified in the trac.config file.
    
    properties = Properties() #get set up with with a properties instance...
    
    def process_testmanager_request(self, req, data ):
        hasTestCases, testCaseSVNpath, errors = self.properties.hasTestCases( self, req )
        data["hasTestCases"] = hasTestCases
        data["testrun_svn_path"] =  testCaseSVNpath
        
        if hasTestCases :
            if req.method == "POST":
                #ok generate some tickets already...
                req.perm.assert_permission('TICKET_CREATE') #but first check to make sure they are allowed to create tickets...
                success, errorMessage_orQueryURL = self.generateTracTickets( req)
                
                if success:
                    #redirect to trac's custom reporting page with the pre-built query that should show the created test cases (and existing tickets that match the query parameters)
                    req.redirect( errorMessage_orQueryURL )
                
                else:
                    data["errorMessage"] = "There is a configuration problem...issues listed below"
                    data["errorsList"] = errorMessage_orQueryURL
                    return "testRunNotConfigured.html", data, None
                
            elif errors != None :
                #self.env.log.info( "ARG!")
                data["errorMessage"] = "There is a configuration problem...issues listed below" 
                data["errorsList"] = errors
                return "testRunNotConfigured.html", data, None
                
            else: 
                # Show Test Run Generation Form: allows a manager to assign testruns to QA staff.
                self.env.log.info( "it wasn't a post....so we know where we are....trying to generate the default page" )
                template, data, content_type = self.provideDefaultCreateTestRunPage( req, data )
                return template, data, content_type
                
        else:
            return "testRunNotConfigured.html", data, None
            #handle when we don't have any test cases...for whatever reason....
            #req.hdf['testcase.run.errormessage'] = "Path in config file is does not exist in subversion...resolved path was: " + path
            #return "testRunNotConfigured.cs", None
            
        return "testrun.html", data, None
        
    def get_path( self, req ):
        return "runs"
    
    def get_descriptive_name(self):
        return "Create Test Run from main line"
    
    
    def provideDefaultCreateTestRunPage( self, req, data ) : 
        """
            this method will retrive a list of users, milestones, versions, testcases, and test templates.
            Test case information and test template information comes from subversion while version and user information comes from TRAC.
        
        """
        testcaseNames = []
        testcaseTemplates = []
        
        #ok now let's extract out of testcases what we need which is mostly testcase ids and template names..
        
        testcases, errors = self.properties.getTestCases( self, req ) #fetch the testcases...

        self.env.log.info( "TESTCASES" + repr(testcases) + " ERRORS : " + repr(errors) )
        
        self.env.log.info( "LENGTH OF TESTCASES : " + str ( len( testcases ) ) )
        
        if testcases == None or len(errors) > 0 : 
            data["errorMessage"] = "No test cases found or other error...see list below if any"
            data["errorsList"] = errors
            return "testRunNotConfigured.html", data, None
            
        for key, testcase in testcases.iteritems():
            testcaseNames.append( testcase.getId() )
            self.env.log.info( "Added test case id : " + testcase.getId()   + " to the list " )
        
        testcaseNames.sort()
                
        templates = self.properties.getTemplates(self, req )
        templateNames = []
        if templates != None : 
            templateNames = templates.getTemplateNames()
        
        milestones = self.properties.getMilestones(self, req )
        milestones.append("")   #this is so there is a blank in the drop down select...default is none...
        versions = self.properties.getVersions(self, req )
        versions.append("")  #ditto
        
        self.env.log.info( "KNOWN USERS : " + repr ( self.properties.getKnownUserNamesOnly(self, req) ) )
        
        data['testrun_users'] = self.properties.getKnownUserNamesOnly(self, req)
        data['testrun_testcases'] = testcaseNames
        data['testrun_testtemplates'] = templateNames
        data['testrun_versions'] = versions
        data['testrun_milestones'] =  milestones
        data['testrun_validatePath'] = req.base_url + "/testmanagement/validate?pathConfiguration=" + self.properties.getTestCasePath(self, req)
                
        return "testrun.html", data, None
        
    def generateTracTickets( self, req ) :
        """
            ok, it's a post so we know we are supposed to go ahead and create some TRAC tickets...the parameters that we care about are:
            #users ...this will be a list...
            #testtemplates ... this will be a list...
            #testcases  ... this will be a list...
            #version...this will be a string...
            #milestone...this will be a string...
            
            This method does one of two things.  It will either return: "True, URL" if ticket creation based on user input was succesful or "False, ErrorMessage" if
            the ticket creation failed.           
            
        """
        
        #grab the parameters that we care about out of the request object
        testRunKeyWord = str( req.args.get('testrun_keyword') )
        users = req.args.get('testrun_users')
        testTemplates = req.args.get('testrun_selectedtemplates')
        testcases = req.args.get('testrun_selectedtestcases')
        version = str( req.args.get('testrun_selectedversion'))
        milestone = str( req.args.get('testrun_selectedmilestone'))
        testConfiguration = str( req.args.get('testrun_testconfiguration'))
        
        #-----------------------------------ERROR CHECKING ON PARAMETERS--------------------------------------------
        #it might make sense to create a new method to validate the parameters passed in but for now we'll leave it.
        
        if testRunKeyWord == None : 
            testRunKeyWord = ""
        testRunKeyWord = self.properties.trimOutAnyProblemStrings(testRunKeyWord)  #this is manually typed in...so it's probably a good idea to look for sqlInjection etc...
        
        if version == None:
            version = ""
        if milestone == None:
            milestone = ""
        if users == None :
            return False, "No users selected for test run"
            
        #check to see if the user, templates or testcases parameters is a str/unicode or a list (well if it isn't a unicode or str then it is a list)
        if isinstance( users, unicode): 
            users = [users]
            
        if isinstance( users, str): 
            users = [TracText.to_unicode ( users )]   

        if isinstance( testcases, unicode) :
            testcases = [testcases]
        
        if isinstance( testcases, str ):
            testcases = [testcases]
        
        if isinstance( testTemplates, unicode) :
            testTemplates = [testTemplates]
            
        if isinstance( testTemplates, str ):
            testTemplates = [TracText.to_unicode ( testTemplates) ]
        
        
        version = TracText.to_unicode ( version).strip()  
        milestone = TracText.to_unicode ( milestone ).strip()

        if testcases == None :
            testcases = [] #so we don't get a blow up later...
            if testTemplates == None :
                return False, "must select at least one testcase or test template to create a test run"
    
        elif testTemplates == None :
            testTemplates = []
    
        #--------------------------------------------DONE ERROR CHECKING -----------------------------------------------
       
    
        #create combined testcase list        
        testcases = self.createCombinedTestCaseList( testTemplates, testcases, req ) 
            
        allTestcases, errors = self.properties.getTestCases( self, req ) #fetch the testcases...
        if errors :
            return False, errors
        
        if allTestcases == None : 
            return False, None
        
        #one last validation step
        errorMessages = []
        for aUser in users : 
            for testId in testcases : 
                testId = TracText.to_unicode( testId ).strip()
                if testId in allTestcases :
                    continue
                else:
                    self.env.log.info( "Testcase : " + testId + "  not found in master list " )
                    errorMessages.append( "The test: " + testId + ", doesn't match it's file name or you've specified it wrong in the testtemplates.xml file" )
        
        if errorMessages:
            return False, errorMessages
        
        #ok this is where we actually create the tickets...
        db = self.env.get_db_cnx()
        for aUser in users : 
            for testId in testcases : 
                testId = testId.encode('ascii', 'ignore').strip()
                if testId in allTestcases :
                
                    test = allTestcases[ testId ]
                    ticket = Ticket(self.env, db=db)
                    ticket.populate(req.args)            
                    ticket.values['reporter'] = req.authname #the reporter is whoever is logged in
                    ticket.values['summary'] = "TestID: " + test.getId() + " -- " + testConfiguration
                    ticket.values['description'] = "''''''Test Details:''''''\n\n" + test.getDescription() + "\n\n''''''Expected result:'''''' \n\n" + test.getExpectedResult()
                    ticket.values['type'] = 'testcase'
                    ticket.values['status'] = 'new'
                    ticket.values['action'] = 'create'
                    ticket.values['component'] = test.getComponent()
                    ticket.values['owner'] = aUser
                    ticket.values['version'] = version
                    ticket.values['milestone'] = milestone
                    ticket.values['keywords'] = testRunKeyWord  
                    #self._validate_ticket(req, ticket)   #probably should validate the ticket here.
                    ticket.insert(db=db)
                    db.commit()
                else:
                    return False, "The test " + testId + " specified in a test template or as the testcaseID in the test file does not exist in the master test list "
        
        #ok blow away the session vars incase someone trys to refresh the created test run page...no need to recreate all the tickets again...
        #thanks to the haxs in the reporty.py module...
        for var in ('users', 'testcases', 'testtemplates','milestone','version'):
                if req.session.has_key(var):
                    del req.session[var]
        
        #redirect to a custom query report showing the created tickets
        return True, req.base_url + "/query?status=new&status=assigned&status=reopened&status=accepted&testcase_result=&version=" + version + "&milestone=" + milestone + "&type=testcase&order=priority&group=owner"

    def createCombinedTestCaseList( self, testTemplates, testcases, req ) :
        
        if len(testTemplates) < 1 :
            return testcases #hopefully testcases isn't < 1 as well...
        else:
            projTemplates = self.properties.getTemplates(self, req )
            tempTestCaseList = []
            for name in testTemplates : 
                name = TracText.to_unicode ( name )
                name  = self.properties.trimOutAnyProblemStrings(name )
                testIds = projTemplates.getTestsForTemplate( name )
                if testIds != None : 
                    for id in testIds : 
                        if id not in tempTestCaseList :
                            tempTestCaseList.append( id )
        
            #ok now add any additional testcases
            if testcases != None :
                for test in testcases :
                    if test not in tempTestCaseList :
                        tempTestCaseList.append( test )
            
            return tempTestCaseList
   