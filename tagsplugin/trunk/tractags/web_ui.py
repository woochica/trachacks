import re
import math
from trac.core import *
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor, \
                            add_stylesheet
from genshi.builder import tag as builder
from trac.util.compat import sorted, set
from tractags.api import TagSystem
from trac.resource import Resource
from trac.mimeview import Context
from trac.wiki.formatter import Formatter


class TagTemplateProvider(Component):
    implements(ITemplateProvider)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('tags', resource_filename(__name__, 'htdocs'))]


class TagRequestHandler(Component):
    implements(IRequestHandler, INavigationContributor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if 'TAGS_VIEW' in req.perm:
            return 'tags'

    def get_navigation_items(self, req):
        if 'TAGS_VIEW' in req.perm('tag'):
            yield ('mainnav', 'tags',
                   builder.a('Tags', href=req.href.tags(), accesskey='T'))

    # IRequestHandler methods
    def match_request(self, req):
        return 'TAGS_VIEW' in req.perm('tags') and req.path_info.startswith('/tags')

    def process_request(self, req):
        self.env.log.debug(req.path_info)
        match = re.match(r'/tags/?(.*)', req.path_info)
        if match.group(1):
            req.redirect(req.href('tags', q=match.group(1)))
        add_stylesheet(req, 'tags/css/tractags.css')
        query = req.args.get('q', '')
        data = {}
        formatter = Formatter(
            self.env, Context.from_request(req, Resource('tag'))
            )
        data['tag_expression'] = query
        from tractags.macros import TagCloudMacro, ListTaggedMacro
        if not query:
            data['tag_body'] = TagCloudMacro(self.env) \
                .expand_macro(formatter, 'TagCloud', '')
        else:
            data['tag_body'] = ListTaggedMacro(self.env) \
                .expand_macro(formatter, 'ListTagged', query)
        return 'tag_cloud.html', data, None
