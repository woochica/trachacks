# -*- coding: utf-8 -*-

# Standard imports.
import re

# Trac imports.
from trac.core import *

# Trac interfaces.
from trac.web.main import IRequestHandler

# Local imports.
from tracdiscussion.api import *

class DiscussionAjax(Component):
    """
        The AJAX module implements AJAX requests handler.
    """
    implements(IRequestHandler)
    
    # IRequestHandler methods.

    def match_request(self, req):
        # Try to match request pattern to request URL.
        match = re.match(r'''/discussion/ajax(?:/(forum|topic|message)/(\d+)(?:/?$))''',
          req.path_info)
        if match:
            resource_type = match.group(1)
            resource_id = match.group(2)
            if resource_type == 'forum':
                req.args['forum'] = resource_id
            if resource_type == 'topic':
                req.args['topic'] = resource_id
            if resource_type== 'message':
                req.args['message'] = resource_id
        return match

    def process_request(self, req):
        # Create request context.
        context = Context.from_request(req)
        context.realm = 'discussion-ajax'
        if req.args.has_key('forum'):
            context.resource = Resource('discussion', 'forum/%s' % (
              req.args['forum'],))
        if req.args.has_key('topic'):
            context.resource = Resource('discussion', 'topic/%s' % (
              req.args['topic'],))
        if req.args.has_key('message'):
            context.resource = Resource('discussion', 'message/%s' % (
              req.args['message'],))

        # Process request and return content.
        api = self.env[DiscussionApi]
        template, data = api.process_discussion(context)

        # Return template and its data.
        return template, data, None
