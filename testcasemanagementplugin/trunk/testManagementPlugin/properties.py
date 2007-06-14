import re

import string
import os
import sys, traceback
import time
import logging
import logging.handlers
from trac import env
from trac.versioncontrol import api
from trac.ticket import Component, Version, Milestone, Ticket, TicketSystem
import xml.dom.minidom
    


class Properties :
    trac_config_testcase_section = 'testManagementExtension'
    trac_config_testcase_property = 'SubversionPathToTestCases'
    
    def getVersions( self, component, req ):
        versions = []
        for v in Version.select(component.env) :
            versions.append(v.name)
        return versions

    def getComponents( self, component, req ):
        components = []
        for c in Component.select(component.env) :
            components.append(c.name)
        return components
        
    def getMilestones(self, component, req ):
        milestones = []
        for m in Milestone.select(component.env) :
            milestones.append(m.name) 
        return milestones
        
    def hasTestCases(self, component, req ):
        #check to see if the path to the testcases has been specified for this component in this project.
             
        testcasePath = self.getTestCasePath( component, req )
        repository = self.getRepository( component, req )
        
        #return repository.has_node( testcasePath ), testcasePath  
        return True, testcasePath
            
    def getTestCasePath(self, component, req):
        #potentially a user wants to use the branch for testcases so check that first
        path = req.args.get('pathConfiguration')
        if path != None:
            return path
        else:
            return component.config.get( self.trac_config_testcase_section , self.trac_config_testcase_property)
    
    def getRepositoryRoot( self, component, req ) :
        return component.config.get( "trac" , "repository_dir" )
    
    def getKnownUserNamesOnly( self, component, req ) :
        tempListNames = []
        users = self.getKnownUsers(component, req)
        for username, name, email in users :
            tempListNames.append( username )
        
        tempListNames.sort()
        return tempListNames
    
    def getKnownUsers(self, component, req ):
        return component.env.get_known_users() # username, name, email
      
    def getRepository( self, component, req ):
        return component.env.get_repository( req.authname ) 
    
    def getTestCases(self, component, req ):

        repository = self.getRepository( component, req )
        node = repository.get_node( self.getTestCasePath( component, req ), repository.youngest_rev )
        entries = node.get_entries()
        
        testcases = {}
        errors = []
        
        #let's create the list of testcases...
        for entry in entries :
            match = re.match('testtemplates.xml',  entry.get_name() )
            #we want to parse testcases not the testtemplate file...
            if not match:
                match = re.match('\S*xml$',  entry.get_name() )  #this allows us to have other files 
                if match:
                    try:
                        content = entry.get_content().read()
                        testcase = TestCase( entry.get_name(), str(content), component )
                        testcases[ testcase.getId().encode('ascii', 'ignore').strip() ] =  testcase 
                    except Exception, ex:
                        errors.append( "The testcsae  :" + entry.get_name() + "  is not well formed xml...a parse error occured " )
                        component.env.log.debug( "The testcsae  :" + entry.get_name() + "  is not well formed xml...a parse error occured " )
                        
                        
        #first let's do some validation on the testcases...
        components = self.getComponents( component, req )
        currentTestcase = None
        component.env.log.debug( "testcases length is : " + repr( len( testcases ) ) )
        try:
            for key, value in testcases.iteritems():
                currentTestcase = value #incase we do toss an exception I'll want some information from this testcase
                components.index( value.getComponent().encode('ascii', 'ignore').strip() ) #this will toss an exception if the component in the testcase doesn't exist in the trac project
        except Exception, ex:
            errors.append( "The component :" + currentTestcase.getComponent() + ", in the testcase : " + currentTestcase.getId() + ", does not exist in the trac project "  )
            component.env.log.debug( "The component :" + currentTestcase.getComponent() + ", in the testcase : " + currentTestcase.getId() + ", does not exist in the trac project "  )
            
        component.env.log.debug( "testcases length is : " + repr( len( testcases ) ) )

        return testcases, errors #ok return the testcases
        
    def getTemplates( self, component, req ):
        #templates.xml is stored in the same directory as the testcases
        repository = self.getRepository( component, req )
        
        node = repository.get_node( self.getTestCasePath( component, req ), repository.youngest_rev )
        entries = node.get_entries()
        
        templates = []
        
        #ok spin through the entries we only care about one called testtemplates.xml
        for entry in entries :
            match = re.match('testtemplates.xml',  entry.get_name() )
            if match:
                content = entry.get_content().read()
                return Templates( str(content), component ) #there should only be one testtemplates.xml file...
            #else:
            #    component.env.log.debug( "didn't care about : " + entry.get_name() )
        
        return None
        
    #todo...maybe look at how validateTestCases could be used in getTestCases.  Can't right now because a circular dependency would be created.
    def validateTestCases( self, component, req ):
    
        try:
            tempTestCaseList = []
            errors = []
            
            projTemplates = self.getTemplates(component, req )
            
            if projTemplates != None :         
                for name in projTemplates.getTemplateNames() : 
                    name = name.encode('ascii', 'ignore')
                    testIds = projTemplates.getTestsForTemplate( name )
                    if testIds != None : 
                        for id in testIds : 
                            if id not in tempTestCaseList :
                                tempTestCaseList.append( id )
    
                allTestcases, errors = self.getTestCases( component, req ) #fetch the testcases...
            
                if allTestcases == None : 
                    return False, None
                
                for testId in tempTestCaseList:
                    if testId in allTestcases : 
                        continue
                    else:
                        errors.append( "The test: " + testId + ", in the testtemplates.xml file cannont be matched with a real test case" )
            else:
                #ok if no testtemplates file exists we should definately flag that.  However rather than bail we could also still validate 
                #the existing testcases to make sure they are well formed.
                allTestcases, errors = self.properties.getTestCases( self, req ) #fetch the testcases...
                
                #append the error message saying testtemplates.xml doesn't exist, then exit.
                errors.append( "No file called testtemplates.xml file found.  This is the file necessary for grouping testcases into predefined test scripts...like a smoke test" )
                
        except Exception, ex:
            errors.append( "An uspecified error occured...the most likely cause is either the path subversionpathtotestcases or repository_dir configuration values are set wrong in the trac.conf file.  Error message included hopefully it will be useful")
            errors.append( "Exception was: " + str(ex) )
            
        return errors
        
        
class Templates:
    
    def getTestsForTemplate( self, templateName ):
        if templateName in self.templates:
            return self.templates[templateName]
        else:
            return None
        
    
    def getTemplateNames(self) :
        keys = self.templates.keys()
        keys.sort()
        return keys


    def __init__( self, templatecontent, component ):
        self.templates = {}
                
        templateDOM = xml.dom.minidom.parseString( templatecontent )
        
        nodes = templateDOM.getElementsByTagName( 'testcases' ) #this fetches all the testcases elements...
        
        for aNode in nodes:
            templateName = aNode.parentNode.getAttribute('name') #this should be the name of the template
            tempTestCaseList = []
            #component.env.log.debug( "Template name : " + templateName )
            
            for test in aNode.childNodes:            
                if test.nodeType == xml.dom.minidom.Node.ELEMENT_NODE :
                    for child in test.childNodes:
                        if child.nodeType == xml.dom.minidom.Node.TEXT_NODE :
                            tempTestCaseList.append( child.data )
                        #else...again we don't care about other kinds of nodes.
                #else don't care about other kinds of nodes...
                self.templates[ templateName ] = tempTestCaseList #ok add our new template with the list of testcases for that template...
            #end for loop...

class TestCase :
    #accessor methods for private properties
    def getId(self) : 
        return self.id.encode('ascii', 'ignore').strip()
    
    def getSummary(self):
        return self.summary
    
    def getDescription(self):
        return self.description

    def getComponent(self):
        return self.component
    
    def getExpectedResult(self):
        return self.expectedresult
        
    def __init__(self, testcasename, testCaseContent, component ) : 
        self.id = ""
        self.summary = ""
        self.description = ""
        self.expectedresult = ""
        self.component = ""

        attributesList = ['id', 'summary','description','expectedresult', 'component']
        
        #ok let's extract out of the xml doco what we need.  Since the format of the xml is trivial this is a nice convienent way to parse the xml.
        testcaseDOM = xml.dom.minidom.parseString(testCaseContent)
        for a in attributesList : 
            nodes = testcaseDOM.getElementsByTagName( a )
            for aNode in nodes:
                #should only be one node...
                for child in aNode.childNodes:
                    if child.nodeType == xml.dom.minidom.Node.TEXT_NODE :
                        self.__dict__[a] += child.data
                    #else...we don't care about other kinds of nodes...not that there should be any.
        
        testcaseDOM.unlink()
        

if __name__ == '__main__':
    sys.exit( main( sys.argv ) )