# -*- coding: utf-8 -*-

# Standard imports.
import re
from pkg_resources import resource_filename

# Trac imports.
from trac.core import *
from trac.config import Option
from trac.resource import Resource
from trac.mimeview.api import Mimeview, Context
from trac.util.html import html
from trac.util.translation import _

# Trac interfaces.
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.mimeview.api import IContentConverter

# Local imports.
from tracdiscussion.api import *

class DiscussionCore(Component):
    """
        The core module implements a message board, including wiki links to
        discussions, topics and messages.
    """
    implements(ITemplateProvider, INavigationContributor, IContentConverter,
      IRequestHandler)

    # Configuration options.

    title = Option('discussion', 'title', _('Discussion'),
      _('Main navigation bar button title.'))

    # ITemplateProvider methods.

    def get_htdocs_dirs(self):
        return [('discussion', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods.

    def get_active_navigation_item(self, req):
        return 'discussion'

    def get_navigation_items(self, req):
        if req.perm.has_permission('DISCUSSION_VIEW'):
            yield 'mainnav', 'discussion', html.a(self.title,
              href = req.href.discussion())

    # IContentConverter methods.

    def get_supported_conversions(self):
        yield ('rss', _('RSS Feed'), 'xml', 'tracdiscussion.topic',
          'application/rss+xml', 8)
        yield ('rss', _('RSS Feed'), 'xml', 'tracdiscussion.forum',
          'application/rss+xml', 5)

    def convert_content(self, req, mimetype, resource, key):
        if key == 'rss':
            return self._export_rss(req, resource)

    # IRequestHandler methods.

    def match_request(self, req):
        if req.path_info == '/discussion/redirect':
            # Proces redirection request.
            req.redirect(req.args.get('redirect_url'))
        else:
            # Try to match request pattern to request URL.
            match = re.match(r'''/discussion(?:/?$|/(forum|topic|message)/(\d+)(?:/?$))''',
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
        context.realm = 'discussion-core'
        if req.args.has_key('forum'):
            context.resource = Resource('discussion', 'forum/%s' % (
              req.args['forum'],))
        if req.args.has_key('topic'):
            context.resource = Resource('discussion', 'topic/%s' % (
              req.args['topic'],))
        if req.args.has_key('message'):
            context.resource = Resource('discussion', 'message/%s' % (
              req.args['message'],))

        # Redirect to content converter if requested.
        if req.args.has_key('format'):
            if req.args.has_key('topic'):
                Mimeview(self.env).send_converted(req, 'tracdiscussion.topic',
                  context.resource, req.args.get('format'), filename = None)
            elif req.args.has_key('forum'):
                Mimeview(self.env).send_converted(req, 'tracdiscussion.forum',
                  context.resource, req.args.get('format'), filename = None)

        # Process request and return content.
        api = self.env[DiscussionApi]
        template, data = api.process_discussion(context)

        if context.redirect_url:
            # Redirect if needed.
            href = req.href(context.redirect_url[0]) + context.redirect_url[1]
            self.log.debug(_("Redirecting to %s") % (href))
            req.redirect(req.href('discussion', 'redirect', redirect_url =
              href))
        else:
            # Add links to other formats.
            if context.forum or context.topic or context.message:
                for conversion in Mimeview(self.env).get_supported_conversions(
                  'tracdiscussion.topic'):
                    format, name, extension, in_mimetype, out_mimetype, \
                      quality, component = conversion
                    conversion_href = get_resource_url(self.env,
                      context.resource,  context.req.href, format = format)
                    add_link(context.req, 'alternate', conversion_href, name,
                      out_mimetype, format)

            # Return template and its data.
            return template, data, None

    # Internal methods.
    def _export_rss(self, req, resource):
        # Create request context.
        context = Context.from_request(req)
        context.realm = 'discussion-core'
        context.resource = resource

        # Process request and get template and template data.
        api = self.env[DiscussionApi]
        template, data = api.process_discussion(context)

        # Render template and return RSS feed.
        output = Chrome(self.env).render_template(req, template, data,
          'application/rss+xml')
        return output, 'application/rss+xml'
