# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re
import math
from trac.core import *
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor, \
                            add_stylesheet, add_ctxtnav
from genshi.builder import tag as builder
from trac.util import to_unicode
from trac.util.text import CRLF
from trac.util.compat import sorted, set, any
from tractags.api import TagSystem, ITagProvider
from tractags.query import InvalidQuery
from trac.resource import Resource
from trac.mimeview import Context
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage


class TagTemplateProvider(Component):
    """Provides templates and static resources for the tags plugin."""

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
    """Implements the /tags handler."""

    implements(IRequestHandler, INavigationContributor)

    tag_providers = ExtensionPoint(ITagProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if 'TAGS_VIEW' in req.perm:
            return 'tags'

    def get_navigation_items(self, req):
        if 'TAGS_VIEW' in req.perm:
            yield ('mainnav', 'tags',
                   builder.a('Tags', href=req.href.tags(), accesskey='T'))

    # IRequestHandler methods
    def match_request(self, req):
        return 'TAGS_VIEW' in req.perm and req.path_info.startswith('/tags')

    def process_request(self, req):
        req.perm.require('TAGS_VIEW')
        add_ctxtnav(req, 'Cloud', req.href.tags())
        match = re.match(r'/tags/?(.*)', req.path_info)
        if match.group(1):
            req.redirect(req.href('tags', q=match.group(1)))
        add_stylesheet(req, 'tags/css/tractags.css')
        query = req.args.get('q', '')
        data = {'title': 'Tags'}
        formatter = Formatter(
            self.env, Context.from_request(req, Resource('tag'))
            )

        realms = [p.get_taggable_realm() for p in self.tag_providers]
        checked_realms = [r for r in realms if r in req.args] or realms
        data['tag_realms'] = [{'name': realm, 'checked': realm in checked_realms}
                              for realm in realms]

        single_page = re.match(r"""(['"]?)(\w+)\1$""", query)
        if single_page:
            page_name = single_page.group(2)
            page = WikiPage(self.env, page_name)
            data['tag_page'] = page

        if query:
            data['tag_title'] = 'Showing objects matching "%s"' % query
        data['tag_query'] = query

        from tractags.macros import TagWikiMacros
        macros = TagWikiMacros(self.env)
        if not query:
            macro = 'TagCloud'
        else:
            macro = 'ListTagged'
        query = '(%s) (%s)' % (' or '.join(['realm:' + r for r in realms
                                            if r in checked_realms]), query)
        self.env.log.debug('Tag query: %s', query)
        try:
            data['tag_body'] = macros.expand_macro(formatter, macro, query)
        except InvalidQuery, e:
            data['tag_query_error'] = to_unicode(e)
            data['tag_body'] = macros.expand_macro(formatter, 'TagCloud', '')
        return 'tag_view.html', data, None
