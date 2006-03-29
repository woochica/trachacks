#Copyright (C) 2006 Gabriel Golcher
#Copyright (C) 2006 Anthony Panozzo
#Copyright (C) 2006 Adam Westhusing
#All rights reserved. 

#This file is part of The Trac Peer Review Plugin

#The Trac Peer Review Plugin is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#The Trac Peer Review Plugin is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with The Trac Peer Review Plugin; if not, write to the Free Software
#Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# Provides functionality to create a new code review.
# Works with peerReviewNew.cs

from trac.core import *
from trac.web.chrome import INavigationContributor,ITemplateProvider
from trac.web.main import IRequestHandler
from trac import util
from trac.util import escape
from codereview.CodeReviewStruct import *
from codereview.dbBackend import *
from codereview.ReviewerStruct import *
from trac.web.chrome import add_stylesheet
import time

class UserbaseModule(Component):
    implements(IRequestHandler, ITemplateProvider, INavigationContributor)
    

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return [] 
       

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/peerReviewNew'
                                        

    def process_request(self, req):
        if req.perm.has_permission('CODE_REVIEW_MGR'):
            req.hdf['manager'] = 1
        else:
            req.perm.assert_permission('CODE_REVIEW_DEV')
            req.hdf['manager'] = 0

        # set up the dynamic links
        req.hdf['trac.href.peerReviewMain'] = self.env.href.peerReviewMain()
        req.hdf['trac.href.peerReviewNew'] = self.env.href.peerReviewNew()
        req.hdf['trac.href.peerReviewSearch'] = self.env.href.peerReviewSearch()
        req.hdf['trac.href.peerReviewOptions'] = self.env.href.peerReviewOptions()

        req.hdf['main'] = "no"
        req.hdf['create'] = "yes"
        req.hdf['search'] = "no"
        req.hdf['options'] = "no"
            
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        allUsers = dbBack.getPossibleUsers()
        reviewID = req.args.get('resubmit')
        req.hdf['oldid'] = -1

        # if we tried resubmitting and the reviewID is not a valid number or not a valid code review, error
        if reviewID != None and (not reviewID.isdigit() or dbBack.getCodeReviewsByID(reviewID) == None):
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "Resubmit ID error"
            req.hdf['error.message'] = "Invalid resubmit ID supplied - unable to load page correctly."
            return 'error.cs', None
            
        # if we are resubmitting a code review and we are the author or the manager
        if reviewID != None and (dbBack.getCodeReviewsByID(reviewID).Author == util.get_reporter_id(req) or req.perm.has_permission('CODE_REVIEW_MGR')):
            review = dbBack.getCodeReviewsByID(reviewID)
            req.hdf['new'] = "no"
            req.hdf['oldid'] = reviewID
            # get code review data and populate
            userStructs = dbBack.getReviewers(reviewID)
            returnUsers = ""
            popUsers = []
            for struct in userStructs:
                returnUsers+=struct.Reviewer + "#"
                popUsers.append(struct.Reviewer)
            files = dbBack.getReviewFiles(reviewID)
            returnFiles = ""
            popFiles = []
            # Set up the file information
            for struct in files:
                returnFiles+=struct.Path + "," + struct.Version + "," + struct.LineStart + "," + struct.LineEnd + "#"
                tempFiles = []
                tempFiles.append(struct.Path)
                tempFiles.append(struct.Version)
                tempFiles.append(struct.LineStart)
                tempFiles.append(struct.LineEnd)
                popFiles.append(tempFiles);
            req.hdf['files'] = returnFiles
            req.hdf['name'] = review.Name
            req.hdf['notes'] = review.Notes
            req.hdf['reviewers'] = returnUsers
            req.hdf['prevUsers'] = popUsers
            req.hdf['prevFiles'] = popFiles

            # Figure out the users that were not included
            # in the previous code review so that they can be
            # added to the dropdown to select more users
            # (only check if all users were not included in previous code review)
            notUsers = []
            if len(popUsers) != len(allUsers): 
                for user in allUsers:
                    match = "no"
                    for candidate in popUsers:
                        if candidate == user:
                            match = "yes"
                            break
                    if match == "no":
                        notUsers.append(user)
                req.hdf['notPrevUsers'] = notUsers
                req.hdf['emptyList'] = 0
            else:
                req.hdf['notPrevUsers'] = []
                req.hdf['emptyList'] = 1    
        else:
            if req.args.get('reqAction') == 'createCodeReview':
                oldid = req.args.get('oldid')
                if oldid != None:
                    review = dbBack.getCodeReviewsByID(oldid)
                    review.Status = "Closed"
                    review.save(db)
                returnid = self.createCodeReview(req);
                #If no errors then redirect to the viewCodeReview page
                req.redirect(self.env.href.peerReviewView() + '?Review=' + returnid)
            req.hdf['new'] = "yes"     
        req.hdf['users'] = allUsers
        req.hdf['trac.href.peerReviewBrowser'] = self.env.href.peerReviewBrowser()
	add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        return 'peerReviewNew.cs', None
                

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # Needed to be filled out based on interface
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]


    # Takes the information given when the page is posted
    # and creates a new code review struct in the database
    # and populates it with the information.  Also creates
    # new reviewer structs and file structs for the review.
    def createCodeReview(self, req):
        struct = CodeReviewStruct(None)
        struct.Author = util.get_reporter_id(req)
        struct.Status = 'Open for Review'
        struct.DateCreate = int(time.time())
        struct.Name = req.args.get('Name')
        struct.Notes = req.args.get('Notes')
        id = struct.save(self.env.get_db_cnx())
        
        # loop here through all the reviewers
        # and create new reviewer structs based on them
        string = req.args.get('ReviewersSelected')
        tokens = string.split('#')
        for token in tokens:
            if token != "":
                struct = ReviewerStruct(None)
                struct.IDReview = id
                struct.Reviewer = token
                struct.Status = 'Not Reviewed'
                struct.Vote = "-1"
                struct.save(self.env.get_db_cnx())

        # loop here through all included files
        # and create new file structs based on them
        files = req.args.get('FilesSelected')
        items = files.split('#')
        for item in items:
            if item != "":
                segment = item.split(',')
                struct = ReviewFileStruct(None)
                struct.IDReview = id
                struct.Path = segment[0]
                struct.Version = segment[1]
                struct.LineStart = segment[2]
                struct.LineEnd = segment[3]
                struct.save(self.env.get_db_cnx())

        return id    
