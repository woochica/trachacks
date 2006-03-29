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

# Provides functionality for main page
# Works with peerReviewMain.cs

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor
from trac import util
from trac.util import escape, Markup
from codereview.dbBackend import *
from trac.web.chrome import add_stylesheet


class UserbaseModule(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, IPermissionRequestor)
        
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'peerReviewMain'
                
    def get_navigation_items(self, req):
        if not (req.perm.has_permission('CODE_REVIEW_DEV') or req.perm.has_permission('CODE_REVIEW_MGR')):
            return
        yield ('mainnav', 'peerReviewMain',
               Markup('<a href="%s">Peer Review</a>',
                      self.env.href.peerReviewMain()))
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/peerReviewMain'


    # IPermissionRequestor methods
    def get_permission_actions(self):
         return ['CODE_REVIEW_DEV', 'CODE_REVIEW_MGR']
                                        

    def process_request(self, req):
        # test whether this user is a manager or not
        if req.perm.has_permission('CODE_REVIEW_MGR'):
            req.hdf['author'] = "manager"
            req.hdf['manager'] = 1
        else:
            req.perm.assert_permission('CODE_REVIEW_DEV')
            req.hdf['author'] = "notmanager"
            req.hdf['manager'] = 0

        # set up dynamic links
        req.hdf['trac.href.peerReviewMain'] = self.env.href.peerReviewMain()
        req.hdf['trac.href.peerReviewNew'] = self.env.href.peerReviewNew()
        req.hdf['trac.href.peerReviewSearch'] = self.env.href.peerReviewSearch()
        req.hdf['trac.href.peerReviewOptions'] = self.env.href.peerReviewOptions()

        req.hdf['main'] = "yes"
        req.hdf['create'] = "no"
        req.hdf['search'] = "no"
        req.hdf['options'] = "no"

        req.hdf['trac.href.peerReviewView'] = self.env.href.peerReviewView()
        req.hdf['username'] = util.get_reporter_id(req)

        db = self.env.get_db_cnx()
        codeReview = CodeReviewStruct(None)
        dbBack = dbBackend(db)
        codeReviewArray = dbBack.getMyCodeReviews(util.get_reporter_id(req))
        assignedReviewArray = dbBack.getCodeReviews(util.get_reporter_id(req))
        managerReviewArray = dbBack.getCodeReviewsByStatus("Ready for inclusion")
        reviewReturnArray = []
        assignedReturnArray = []
        managerReturnArray = []
        dataArray = []

        # fill the table of currently open reviews
        for struct in codeReviewArray:
            if struct.Status != "Closed":
                dataArray.append(struct.IDReview)
                dataArray.append(struct.Author)
                dataArray.append(struct.Status)
                dataArray.append(util.format_date(struct.DateCreate))
                dataArray.append(struct.Name)
                reviewReturnArray.append(dataArray)
                dataArray = []
                dataArray = []
        
        # fill the table of code reviews currently assigned to you
        for struct in assignedReviewArray:
            if struct.Status != "Closed":
                dataArray.append(struct.IDReview)
                dataArray.append(struct.Author)
                dataArray.append(struct.Name)
                dataArray.append(util.format_date(struct.DateCreate))            
                reviewstruct = dbBack.getReviewerEntry(struct.IDReview, util.get_reporter_id(req))
                if reviewstruct.Vote == "-1":
                    dataArray.append('Not voted')
                elif reviewstruct.Vote == "0":
                    dataArray.append('Rejected')
                elif reviewstruct.Vote == "1":
                    dataArray.append('Accepted')
                assignedReturnArray.append(dataArray)
                dataArray = []
                dataArray = []

        # fill the table of reviews assigned to you in a manager role
        for struct in managerReviewArray:
            if struct.Status != "Closed":
                dataArray.append(struct.IDReview)
                dataArray.append(struct.Author)
                dataArray.append(struct.Name)
                dataArray.append(util.format_date(struct.DateCreate))
                managerReturnArray.append(dataArray)
                dataArray = []

        req.hdf['reviewReturnArrayLength'] = len(reviewReturnArray)
        req.hdf['assignedReturnArrayLength'] = len(assignedReturnArray)
        req.hdf['managerReviewArrayLength'] = len(managerReviewArray)

        req.hdf['myCodeReviews'] = reviewReturnArray
        req.hdf['assignedReviews'] = assignedReturnArray
        req.hdf['managerReviews'] = managerReturnArray
        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')	
        return 'peerReviewMain.cs', None
                
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
