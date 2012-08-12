#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#

# Provides functionality for view code review page
# Works with peerReviewView.cs

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

    number = -1
    files = []
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return [] 
       
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/peerReviewView'
                                        
    def process_request(self, req):
        # check to see if the user is a manager of this page or not
        if req.perm.has_permission('CODE_REVIEW_MGR'):
            req.hdf['manager'] = 1
        else:
            req.perm.assert_permission('CODE_REVIEW_DEV')
            req.hdf['manager'] = 0

        # set up dynamic links
        req.hdf['trac.href.peerReviewMain'] = self.env.href.peerReviewMain()
        req.hdf['trac.href.peerReviewNew'] = self.env.href.peerReviewNew()
        req.hdf['trac.href.peerReviewSearch'] = self.env.href.peerReviewSearch()
        req.hdf['trac.href.peerReviewPerform'] = self.env.href.peerReviewPerform()
        req.hdf['trac.href.peerReviewView'] = self.env.href.peerReviewView()
        req.hdf['trac.href.peerReviewOptions'] = self.env.href.peerReviewOptions()

        # reviewID argument checking
        reviewID = req.args.get('Review')
        if reviewID == None or not reviewID.isdigit():
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "Review ID error"
            req.hdf['error.message'] = "Invalid review ID supplied - unable to load page."
            return 'error.cs', None

        req.hdf['main'] = "no"
        req.hdf['create'] = "no"
        req.hdf['search'] = "no"
        req.hdf['options'] = "no"

        # set up to display the files that are in this review
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        files = dbBack.getReviewFiles(reviewID)
        returnfiles = []
        newfile = []
        for struct in files:
            newfile.append(struct.IDFile)
            newfile.append(struct.IDReview)
            newfile.append(struct.Path)
            newfile.append(struct.LineStart)
            newfile.append(struct.LineEnd)
            newfile.append(struct.Version)
            newfile.append(len(dbBack.getCommentsByFileID(struct.IDFile)))
            returnfiles.append(newfile)
            newfile = []
        req.hdf['files'] = returnfiles
        req.hdf['filesLength'] = len(returnfiles)
        req.hdf['reviewID'] = reviewID

        req.hdf['users'] = dbBack.getPossibleUsers()
        review = dbBack.getCodeReviewsByID(reviewID)
        # error if review id does not exist in the database
        if review == None:
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "Review error"
            req.hdf['error.message'] = "Review does not exist in database - unable to load page."
            return 'error.cs', None

        # set up the fields that will be displayed on the page
        req.hdf['name'] = review.Name
        req.hdf['notes'] = review.Notes
        req.hdf['status'] = review.Status
        req.hdf['author'] = review.Author
        req.hdf['myname'] = util.get_reporter_id(req)
        req.hdf['datecreate'] = util.format_date(review.DateCreate)
        req.hdf['voteyes'] = dbBack.getVotesByID("1", reviewID)
        req.hdf['voteno'] = dbBack.getVotesByID("0", reviewID)
        req.hdf['notvoted'] = dbBack.getVotesByID("-1", reviewID)
        req.hdf['total_votes_possible'] = float(req.hdf['voteyes']) + float(req.hdf['voteno']) + float(req.hdf['notvoted'])
        req.hdf['threshold'] = float(dbBack.getThreshold())/100

        # figure out whether I can vote on this review or not
        entry = dbBack.getReviewerEntry(reviewID, req.hdf['myname'])
        if entry != None:
            req.hdf['canivote'] = 1
            req.hdf['myvote'] = entry.Vote
        else:
            req.hdf['canivote'] = 0

        #display vote summary only if I have voted or am the author/manager, or if the review is "Ready for inclusion" or "Closed
        req.hdf['viewvotesummary'] = 0
        if req.hdf['author'] == req.hdf['myname'] or req.hdf['manager'] == '1' or (dbBack.getReviewerEntry(reviewID, req.hdf['myname']) != None and dbBack.getReviewerEntry(reviewID, req.hdf['myname']).Vote != '-1') or req.hdf['status']=="Closed" or req.hdf['status']=="Ready for inclusion":
            req.hdf['viewvotesummary'] = 1
        else:
            req.hdf['viewvotesummary'] = 0

        rvs = []  # reviewer/vote pairs
        reviewers = dbBack.getReviewers(reviewID)
        newrvpair = []

        # if we are the manager, list who has voted and what their vote was.
        # if we are the author, list who has voted and who has not.
        # if we are neither, list the users who are participating in this review. 
        if req.hdf['manager'] == '1':
            for reviewer in reviewers:
                newrvpair.append(reviewer.Reviewer)
                if reviewer.Vote == '-1':
                    newrvpair.append("Not voted")
                elif reviewer.Vote == '0':
                    newrvpair.append("No")
                elif reviewer.Vote == '1':
                    newrvpair.append("Yes")
                rvs.append(newrvpair)
                newrvpair = []
        elif review.Author == util.get_reporter_id(req):
            for reviewer in reviewers:
                newrvpair.append(reviewer.Reviewer)
                if reviewer.Vote == '-1':
                    newrvpair.append("Not voted")
                else:
                    newrvpair.append("Voted")
                rvs.append(newrvpair)
                newrvpair = []
        else:
            for reviewer in reviewers:
                newrvpair.append(reviewer.Reviewer)
                rvs.append(newrvpair)
                newrvpair = []

        req.hdf['rvs'] = rvs
        req.hdf['rvsLength'] = len(rvs)


        # execute based on URL arguments
        if req.args.get('Vote') == 'yes':
            self.vote("1", reviewID, req)
        if req.args.get('Vote') == 'no':
            self.vote("0", reviewID, req)

        # process state (Open for review, ready for inclusion, etc.) change by manager
        mc = req.args.get('ManagerChoice')
        if mc == "Open for review" or mc == "Reviewed" or mc == "Ready for inclusion" or mc == "Closed":
            self.manager_change_status(mc, reviewID, req)

        if req.args.get('Close') == '1':
            self.close_review(reviewID, req)

        if req.args.get('Inclusion') == '1':
            self.submit_for_inclusion(reviewID, req)

	add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        return 'peerReviewView.cs', None
                
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

    # If user has not voted for this review and is a voting member, and attempts
    # to vote, change the vote type in the review entry struct in the database
    # and reload the page.
    def vote(self, type, number, req):
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        reviewEntry = dbBack.getReviewerEntry(number, req.hdf['myname'])
        if reviewEntry != None:
            reviewEntry.Vote = type
            reviewEntry.save(db)

        reviewID = req.args.get('Review')
        review = dbBack.getCodeReviewsByID(reviewID)

        voteyes = dbBack.getVotesByID("1", reviewID)
        voteno = dbBack.getVotesByID("0", reviewID)
        notvoted = dbBack.getVotesByID("-1", reviewID)
        total_votes_possible = float(voteyes) + float(voteno) + float(notvoted)
        threshold = float(dbBack.getThreshold())/100

        # recalculate vote ratio, while preventing divide by zero tests, and change status if necessary
        if total_votes_possible != 0:
            vote_ratio = float(voteyes)/float(total_votes_possible)
            if (vote_ratio >= threshold):
                review.Status = "Reviewed"
            else:
                review.Status = "Open for review"
            review.save(db)
        req.redirect(req.hdf['trac.href.peerReviewView'] + "?Review=" + reviewID)
            
    # If it is confirmed that the user is the author of this review and they
    # have attempted to submit for inclusion, change the status of this review
    # to "Ready for inclusion" and reload the page.
    def submit_for_inclusion(self, number, req):
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        review = dbBack.getCodeReviewsByID(number)
        if review.Author == util.get_reporter_id(req):
            if review.Status == "Reviewed":
                review.Status = "Ready for inclusion"
                review.save(db)
                req.redirect(req.hdf['trac.href.peerReviewView'] + "?Review=" + number)

    # If the user is confirmed to be the author or manager and tries to close
    # this review, close it by changing the status of the review to "Closed."
    def close_review(self, number, req):
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        review = dbBack.getCodeReviewsByID(number)
        # this option available if you are the author or manager of this code review
        if review.Author == util.get_reporter_id(req) or req.hdf('Manager') == '1':
            review.Status = "Closed"
            review.save(db)
            req.redirect(req.hdf['trac.href.peerReviewView'] + "?Review=" + number)
            
    # It has already been confirmed that this user is a manager, so this routine
    # just changes the status of the review to the type specified by the manager.
    def manager_change_status(self, type, number, req):
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        review = dbBack.getCodeReviewsByID(number)
        review.Status = type
        review.save(db)
        req.redirect(req.hdf['trac.href.peerReviewView'] + "?Review=" + number)
        
