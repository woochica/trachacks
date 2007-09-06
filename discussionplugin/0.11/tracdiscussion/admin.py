# -*- coding: utf8 -*-

import time

from trac.core import *
from trac.context import Context
from trac.web.chrome import add_stylesheet
from trac.wiki import wiki_to_html, wiki_to_oneliner

from trac.perm import IPermissionRequestor
from trac.admin import IAdminPanelProvider

from tracdiscussion.api import *

class DiscussionWebAdmin(Component):
    """
        The webadmin module implements discussion plugin administration
        via WebAdminPlugin.
    """
    implements(IAdminPanelProvider)

    # IAdminPageProvider
    def get_admin_panels(self, req):
        if req.perm.has_permission('DISCUSSION_ADMIN'):
            yield ('discussion', 'Discussion System', 'group', 'Forum Groups')
            yield ('discussion', 'Discussion System', 'forum', 'Forums')

    def render_admin_panel(self, req, category, page, path_info):
        # Prepare request object
        if page == 'forum':
            if not req.args.has_key('group'):
                req.args['group'] = '-1'
            if path_info:
                req.args['forum'] = path_info
        else:
            if path_info:
                req.args['group'] = path_info

        # Create request context.
        context = Context(self.env, req)('discussion-admin')

        # Process request.
        api = self.env[DiscussionApi]
        return api.process_discussion(context)
