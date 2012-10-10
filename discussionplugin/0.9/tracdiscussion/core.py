# -*- coding: utf-8 -*-

from tracdiscussion.api import *
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor
import re

class DiscussionCore(Component):
    """
        The core module implements a message board, including wiki links to
        discussions, topics and messages.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
      IPermissionRequestor)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['DISCUSSION_VIEW', 'DISCUSSION_APPEND', 'DISCUSSION_MODERATE',
          'DISCUSSION_ADMIN']

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('discussion', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'discussion'

    def get_navigation_items(self, req):
        if req.perm.has_permission('DISCUSSION_VIEW'):
            yield 'mainnav', 'discussion', Markup('<a href="%s">%s</a>' % \
              (self.env.href.discussion(), self.env.config.get('discussion',
              'title', 'Discussion')))

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'''/discussion(?:/?$|/(\d+)(?:/?$|/(\d+))(?:/?$|/(\d+)))$''',
          req.path_info)
        if match:
            forum = match.group(1)
            topic = match.group(2)
            message = match.group(3)
            if forum:
                req.args['forum'] = forum
            if topic:
                req.args['topic'] = topic
            if message:
                req.args['message'] = message
        return match

    def process_request(self, req):
        # Prepare request object
        req.args['component'] = 'core'

        # Get database access
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Return page content
        api = DiscussionApi(self, req)
        content = api.render_discussion(req, cursor)
        db.commit()
        return content