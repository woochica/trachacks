#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#

# This class displays the manager options, which currently consist
# of only the threshold setting.

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac import util
from trac.util import escape
from codereview.dbBackend import *

class UserbaseModule(Component):
    implements(IRequestHandler, ITemplateProvider, INavigationContributor)
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/peerReviewOptions'

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'peerReviewMain'
                
    def get_navigation_items(self, req):
        return []
                                        
    def process_request(self, req):

        data = {}
        #check permissions
        req.perm.assert_permission('CODE_REVIEW_MGR')
        data['manager'] = 1

        # set up the dynamic links
        data['main'] = "no"
        data['create'] = "no"
        data['search'] = "no"
        data['option'] = "yes"

        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
          
        newThreshold = req.args.get('percentage')
       
        #Set the new threshold value
        if (newThreshold != None):
            data['success'] = 1
            dbBack.setThreshold(newThreshold)
            newThreshold = float(newThreshold)/100
            openArray = dbBack.getCodeReviewsByStatus("Open for review")
            for struct in openArray:
                voteyes = float(dbBack.getVotesByID("1", struct.IDReview))
                voteno = float(dbBack.getVotesByID("0", struct.IDReview))
                notvoted = float(dbBack.getVotesByID("-1", struct.IDReview))
                total_votes_possible = voteyes + voteno + notvoted
                if total_votes_possible != 0:
                    vote_ratio = voteyes/total_votes_possible
                # calculate vote ratio, while preventing divide by zero tests
                if (vote_ratio >= newThreshold):
                    struct.Status = "Reviewed"
                    struct.save(db)
            reviewArray = dbBack.getCodeReviewsByStatus("Reviewed")
            for struct in reviewArray:
                voteyes = float(dbBack.getVotesByID("1", struct.IDReview))
                voteno = float(dbBack.getVotesByID("0", struct.IDReview))
                notvoted = float(dbBack.getVotesByID("-1", struct.IDReview))
                total_votes_possible = voteyes + voteno + notvoted
                if total_votes_possible != 0:
                    vote_ratio = voteyes/total_votes_possible
                # calculate vote ratio, while preventing divide by zero tests
                if (vote_ratio < newThreshold):
                    struct.Status = "Open for review"
                    struct.save(db)

        #Get the threshold value
        data['percentage'] = dbBack.getThreshold()

        return 'peerReviewOptions.html', data, None

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
