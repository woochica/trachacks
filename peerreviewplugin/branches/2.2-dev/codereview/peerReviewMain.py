#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#

# Provides functionality for main page
# Works with peerReviewMain.cs

from genshi.builder import tag

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.timeline.api import ITimelineEventProvider
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.resource import *
from trac.util.datefmt import to_timestamp
from trac import util
from trac.util import escape, Markup
from codereview.dbBackend import *
from trac.web.chrome import add_stylesheet
import itertools

class UserbaseModule(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, IPermissionRequestor,ITimelineEventProvider)
        
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'peerReviewMain'
                
    def get_navigation_items(self, req):
        if not (req.perm.has_permission('CODE_REVIEW_DEV') or req.perm.has_permission('CODE_REVIEW_MGR')):
            return
        yield ('mainnav', 'peerReviewMain',
               Markup('<a href="%s">Peer Review</a>') % req.href.peerReviewMain())
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/peerReviewMain'


    # IPermissionRequestor methods
    def get_permission_actions(self):
         return ['CODE_REVIEW_DEV', 'CODE_REVIEW_MGR']
                                        

    def process_request(self, req):

        data = {}
        # test whether this user is a manager or not
        if req.perm.has_permission('CODE_REVIEW_MGR'):
            data['author'] = "manager"
            data['manager'] = 1
        else:
            req.perm.assert_permission('CODE_REVIEW_DEV')
            data['author'] = "notmanager"
            data['manager'] = 0

        data['main'] = "yes"
        data['create'] = "no"
        data['search'] = "no"
        data['option'] = "no"

        data['username'] = util.get_reporter_id(req)

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
            if struct.Status != "Closed" and struct.Status != "Ready for inclusion":
                dataArray.append(struct.IDReview)
                dataArray.append(struct.Author)
                dataArray.append(struct.Name)
                dataArray.append(util.format_date(struct.DateCreate))            
                reviewstruct = dbBack.getReviewerEntry(struct.IDReview, util.get_reporter_id(req))
                if reviewstruct.Vote == -1:
                    dataArray.append('Not voted')
                elif reviewstruct.Vote == 0:
                    dataArray.append('Rejected')
                elif reviewstruct.Vote == 1:
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

        data['reviewReturnArrayLength'] = len(reviewReturnArray)
        data['assignedReturnArrayLength'] = len(assignedReturnArray)
        data['managerReviewArrayLength'] = len(managerReviewArray)

        data['myCodeReviews'] = reviewReturnArray
        data['assignedReviews'] = assignedReturnArray
        data['managerReviews'] = managerReturnArray

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')	

        data['cycle'] = itertools.cycle

        return 'peerReviewMain.html', data, None

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

    # ITimelineEventProvider methods
    def get_timeline_filters(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            yield ('codereview', 'Code Reviews')

    def get_timeline_events(self, req, start, stop, filters):
        if 'codereview' in filters:
            codereview_realm = Resource('codereview')

            db = self.env.get_db_cnx()
            dbBack = dbBackend(db)
            codeReviewDetails = dbBack.getCodeReviewsInPeriod(to_timestamp(start), to_timestamp(stop))

            for codeReview in codeReviewDetails:
                codereview_page = codereview_realm(id=codeReview.IDReview)
                reviewers = dbBack.getReviewers(codeReview.IDReview)

                reviewersList = ''
                for reviewer in reviewers:
                     reviewersList = reviewersList + reviewer.Reviewer + ','
            
                yield('codereview', codeReview.DateCreate, codeReview.Author, (codereview_page, codeReview.Name, codeReview.Notes, reviewersList))

    def render_timeline_event(self, context, field, event):
        codereview_page, name, notes, reviewersList = event[3]

        if field == 'url':
            return context.href.peerReviewView(Review=codereview_page.id)
        if field == 'title':
            return tag('Code review ', tag.em(name), ' has been raised')
        if field == 'description':
            return tag('Assigned to: ', reviewersList, tag.br(), ' Additional notes: ', notes)
