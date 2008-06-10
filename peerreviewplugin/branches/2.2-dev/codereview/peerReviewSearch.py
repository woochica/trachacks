#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#

# This class performs searches for code reviews.
# Queries are passed in through POST and results are
# outputted in clearsilver friendly format.
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.util import escape, format_date
from codereview.dbBackend import *
from codereview.CodeReviewStruct import *
import datetime
import time

class UserbaseModule(Component):
    implements(IRequestHandler, ITemplateProvider, INavigationContributor)
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/peerReviewSearch'

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'peerReviewMain'
                
    def get_navigation_items(self, req):
        return []
                                        
    def process_request(self, req):
        #check permissions
        if req.perm.has_permission('CODE_REVIEW_MGR'):
            req.hdf['manager'] = 1
        else:
            req.perm.assert_permission('CODE_REVIEW_DEV')
            req.hdf['manager'] = 0
            
        #if the doSearch parameter is 'yes', perform the search
        #this parameter is set when someone searches
        if(req.args.get('doSearch') == 'yes'):
            results = self.performSearch(req);
            #if there are no results - fill the return array
            #with blank data.
            if(len(results) == 0):
                noValResult = []
                noValResult.append("No results match query.")
                noValResult.append("")
                noValResult.append("")
                noValResult.append("")
                noValResult.append("")
                results.append(noValResult)        
            req.hdf['results'] = results;
            req.hdf['doSearch'] = 'yes';
            
        #sets links for ClearSilver
        req.hdf['trac.href.peerReviewView'] = self.env.href.peerReviewView()
        req.hdf['trac.href.peerReviewMain'] = self.env.href.peerReviewMain()
        req.hdf['trac.href.peerReviewNew'] = self.env.href.peerReviewNew()
        req.hdf['trac.href.peerReviewSearch'] = self.env.href.peerReviewSearch()
        req.hdf['trac.href.peerReviewOptions'] = self.env.href.peerReviewOptions()
        
        #for the top-right nav links
        req.hdf['main'] = "no"
        req.hdf['create'] = "no"
        req.hdf['search'] = "yes"
        req.hdf['options'] = "no"
        
        #get the database
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        users = dbBack.getPossibleUsers()
        #sets the possible users for the user combo-box
        req.hdf['users'] = users
        #creates a year array containing the last 10
        #years - for the year combo-box
        now = datetime.datetime.now()
        year = now.year;
        years = []
        for i in 0,1,2,3,4,5,6,7,8,9,10:
            years.append(year - i)

        req.hdf['years'] = years
        return 'peerReviewSearch.cs', None
                
    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]

    #Performs the search
    def performSearch(self, req):
        #create a code review struct to hold the search parameters
        crStruct = CodeReviewStruct(None)
        #get the search parameters from POST
        author = req.args.get('Author')
        name = req.args.get('CodeReviewName')
        status = req.args.get('Status')
        month = req.args.get('DateMonth')
        day = req.args.get('DateDay')
        year = req.args.get('DateYear')

        #check for entered date values, if none are set
        #default to 0
        if(month == None):
            month = '0';
        if(day == None):
            day = '0';
        if(year == None):
            year = '0';

        #store date values for ClearSilver - used to reset values to
        #search parameters after a search is performed
        req.hdf['searchValues.month'] = month;
        req.hdf['searchValues.day'] = day;
        req.hdf['searchValues.year'] = year;
        req.hdf['searchValues.status'] = status;
        req.hdf['searchValues.author'] = author;
        req.hdf['searchValues.name'] = name;

        #dates are ints in TRAC - convert search date to int
        fromdate = "-1";

        if((month != '0') and (day != '0') and (year != '0')):
            t = time.strptime(month + '/' + day + '/' + year[2] + year[3], '%x')
            #I have no idea what this is doing - obtained from TRAC source
            fromdate = time.mktime((t[0], t[1], t[2], 23, 59, 59, t[6], t[7], t[8]))
            #convert to string for database lookup
            fromdate = `fromdate`

        selectString = 'Select...'
        req.hdf['dateSelected'] = fromdate;
        #if user has not selected parameter - leave
        #value in struct NULL
        if(author != selectString):
            crStruct.Author = author

        if(name != selectString):
            crStruct.Name = name;

        if(status != selectString):
            crStruct.Status = status

        crStruct.DateCreate = fromdate;
        #get the database
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        #perform search
        results = dbBack.searchCodeReviews(crStruct)
        returnArray = []
        tempArray = []
        
        if(results == None):
            return returnArray
        #fill ClearSilver friendly array with
        #search results
        for struct in results:
            tempArray.append(struct.IDReview)
            tempArray.append(struct.Author)
            tempArray.append(struct.Status)
            tempArray.append(format_date(struct.DateCreate))
            tempArray.append(struct.Name)
            returnArray.append(tempArray)
            tempArray = []
            
        return returnArray;
