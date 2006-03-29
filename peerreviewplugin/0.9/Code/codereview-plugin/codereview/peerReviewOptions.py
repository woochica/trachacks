#Copyright (C) 2006 Gabriel Golcher <golchega@rose-hulman.edu>
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
        #check permissions
        req.perm.assert_permission('CODE_REVIEW_MGR')
        req.hdf['manager'] = 1

        # set up the dynamic links
        req.hdf['trac.href.peerReviewMain'] = self.env.href.peerReviewMain()
        req.hdf['trac.href.peerReviewNew'] = self.env.href.peerReviewNew()
        req.hdf['trac.href.peerReviewSearch'] = self.env.href.peerReviewSearch()
        req.hdf['trac.href.peerReviewOptions'] = self.env.href.peerReviewOptions()

        req.hdf['main'] = "no"
        req.hdf['create'] = "no"
        req.hdf['search'] = "no"
        req.hdf['options'] = "yes"

        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)

        
        newThreshold = req.args.get('percentage')

        #Set the new threshold value
        if (not newThreshold == None):
            req.hdf['success'] = 1
            dbBack.setThreshold(newThreshold)

        #Get the threshold value
        req.hdf['percentage'] = dbBack.getThreshold()

        return 'peerReviewOptions.cs', None
                
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
