#!/usr/bin/env python

import re

import string
import os
import sys, traceback
import time
import logging
import logging.handlers
from trac.ticket import Component, Milestone, Ticket, TicketSystem, ITicketManipulator
from trac.core import *
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
    
    def process_testmanager_request(self, req):
        
        req.hdf['testcase.run.basepath'] = req.base_url  
        
        hasTestCases, path = self.properties.hasTestCases( self, req )
        
        if hasTestCases :
            if req.method == "POST":
                #ok generate some tickets already...
                req.perm.assert_permission('TICKET_CREATE') #but first check to make sure they are allowed to create tickets...
                success, errorMessage_orQueryURL = self.generateTracTickets( req )
                
                if success:
                    #redirect to trac's custom reporting page with the pre-built query that should show the created test cases (and existing tickets that match the query parameters)
                    req.redirect( errorMessage_orQueryURL )
                
                else:
                    req.hdf['testcase.run.errormessage'] = errorMessage_orQueryURL
                    return "testRunNotConfigured.cs", None
                
            else :
                # Show Test Run Generation Form: allows a manager to assign testruns to QA staff.
                return self.provideDefaultCreateTestRunPage( req )
            
        else:
            #handle when we don't have any test cases...for whatever reason....
            req.hdf['testcase.run.errormessage'] = "Path in config file is does not exist in subversion...resolved path was: " + path
            return "testRunNotConfigured.cs", None
            

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
        testRunDescription = str( req.args.get('testrundescription') )
        users = req.args.get('users')
        testTemplates = req.args.get('testtemplates')
        testcases = req.args.get('testcases')
        version = str( req.args.get('selectedversion'))
        milestone = str( req.args.get('selectedmilestone'))
        testConfiguration = str( req.args.get('testconfiguration'))
        
        #-----------------------------------ERROR CHECKING ON PARAMETERS--------------------------------------------
        if version == None:
            version = ""
        if milestone == None:
            milestone = ""
        if users == None :
            return False, "No users selected for test run"
        if isinstance( users, unicode): 
            users = [users.encode('ascii', 'ignore')]
        
        
        version = version.encode('ascii', 'ignore').strip()
        milestone = milestone.encode('ascii', 'ignore').strip()

        if testcases == None :
            testcases = [] #so we don't get a blow up later...
            if testTemplates == None :
                return False, "must select at least one testcase or test template to create a test run"
                return 'errorCreatingTestRun.cs', None
        elif testTemplates == None :
            testTemplates = []
    
        #create combined testcase list        
        testcases = self.createCombinedTestCaseList( testTemplates, testcases, req ) 
            
        allTestcases = self.properties.getTestCases( self, req ) #fetch the testcases...
        if allTestcases == None : 
            return False, None
        #--------------------------------------------DONE ERROR CHECKING -----------------------------------------------
        
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
                    ticket.values['keywords'] = "Test_ver" + version + "_mile_" + milestone
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
        return True, req.base_url + "/query?status=new&status=assigned&status=reopened&testcase_result=&version=" + version + "&milestone=" + milestone + "&type=testcase&order=priority&group=owner"

    def createCombinedTestCaseList( self, testTemplates, testcases, req ) :
        #ok we are expecting lists to be returned for testcase,templates,and users...but if only one user is returned that's no good so check to see if we are dealing with a list or unicode string
        if isinstance( testcases, unicode) :
            testcases = [testcases.encode('ascii', 'ignore')]
        if isinstance( testTemplates, unicode) :
            testTemplates = [testTemplates.encode('ascii', 'ignore')]
        
        if len(testTemplates) < 1 :
            return testcases #hopefully testcases isn't < 1 as well...
        else:
            projTemplates = self.properties.getTemplates(self, req )
            tempTestCaseList = []
            for name in testTemplates : 
                name = name.encode('ascii', 'ignore')
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
        
    def provideDefaultCreateTestRunPage( self, req ) : 
        """
            this method will retrive a list of users, milestones, versions, testcases, and test templates.
            Test case information and test template information comes from subversion while version and user information comes from TRAC.
        
        """
        testcaseNames = []
        testcaseTemplates = []
        
        #ok now let's extract out of testcases what we need which is mostly testcase ids and template names..
        
        testcases = self.properties.getTestCases( self, req ) #fetch the testcases...
        
        if testcases == None : 
            #there was an error of some kind fetching the testcases...    
            return "testRunNotConfigured.cs", None
            
        for key, testcase in testcases.iteritems():
            testcaseNames.append( testcase.getId() )
        testcaseNames.sort()
                
        templates = self.properties.getTemplates(self, req )
        templateNames = []
        if templates != None : 
            templateNames = templates.getTemplateNames()
        
        sprints = self.properties.getMilestones(self, req )
        sprints.append("")   #this is so there is a blank in the drop down select...default is none...
        versions = self.properties.getVersions(self, req )
        versions.append("")  #ditto
        
        req.hdf['testcase.run.users']= self.properties.getKnownUserNamesOnly(self, req)
        req.hdf['testcase.run.testcases']= testcaseNames
        req.hdf['testcase.run.testtemplates']= templateNames
        req.hdf['testcase.run.sprints']= sprints
        req.hdf['testcase.run.versions']= versions
                
        return 'testRuns.cs', None
        

    def get_path( self, req ):
        return "runs"
    
    def get_descriptive_name(self):
        return "Test Runs"