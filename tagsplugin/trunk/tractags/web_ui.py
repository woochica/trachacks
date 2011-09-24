# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
# Copyright (C) 2011 Steffen Hoffmann <hoff.st@web.de>
# Copyright (C) 2011 Itamar Ostricher <itamarost@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re
import math

from genshi.builder import tag as builder
from pkg_resources import resource_filename
from trac.config import ChoiceOption, ListOption, Option
from trac.core import Component, ExtensionPoint, implements
from trac.mimeview import Context
from trac.resource import Resource
from trac.util import to_unicode
from trac.util.compat import sorted, set, any
from trac.util.text import CRLF
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor, \
                            add_stylesheet, add_ctxtnav
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage

from tractags.api import TagSystem, ITagProvider, _, tag_
from tractags.query import InvalidQuery


class TagTemplateProvider(Component):
    """Provides templates and static resources for the tags plugin."""

    implements(ITemplateProvider)

    abstract = True

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('tags', resource_filename(__name__, 'htdocs'))]


class TagRequestHandler(TagTemplateProvider):
    """Implements the /tags handler."""

    implements(INavigationContributor, IRequestHandler)

    tag_providers = ExtensionPoint(ITagProvider)

    default_cols = Option('tags', 'default_table_cols', 'id|description|tags',
        doc="""Select columns and order for table format using a "|"-separated
            list of column names.

            Supported columns: realm, id, description, tags
            """)
    default_format = ChoiceOption('tags', 'default_format',
        ['oldlist', 'compact', 'table'],
        doc="""Set the default format for the handler of the `/tags` domain.

            || `oldlist` (default value) || The original format with a
            bulleted-list of "linked-id description (tags)" ||
            || `compact` || bulleted-list of "linked-description" ||
            || `table` || table... (see corresponding column option) ||
            """)
    exclude_realms = ListOption('tags', 'exclude_realms', [],
        doc="""Comma-separated list of realms to exclude from tags queries
            by default, unless specifically included using "realm:realm-name"
            in a query.""")

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if 'TAGS_VIEW' in req.perm:
            return 'tags'

    def get_navigation_items(self, req):
        if 'TAGS_VIEW' in req.perm:
            label = tag_("Tags")
            yield ('mainnav', 'tags',
                   builder.a(label, href=req.href.tags(), accesskey='T'))

    # IRequestHandler methods
    def match_request(self, req):
        return 'TAGS_VIEW' in req.perm and req.path_info.startswith('/tags')

    def process_request(self, req):
        req.perm.require('TAGS_VIEW')
        # TRANSLATOR: The meta-nav link label.
        add_ctxtnav(req, _("Cloud"), req.href.tags())
        match = re.match(r'/tags/?(.*)', req.path_info)
        if match.group(1):
            req.redirect(req.href('tags', q=match.group(1)))
        add_stylesheet(req, 'tags/css/tractags.css')
        query = req.args.get('q', '')
        data = {'title': _("Tags")}
        formatter = Formatter(
            self.env, Context.from_request(req, Resource('tag'))
            )

        realms = [p.get_taggable_realm() for p in self.tag_providers]
        if not 'q' in req.args or [r for r in realms if r in req.args] == []: 
            for realm in realms:
                if not realm in self.exclude_realms:
                    req.args[realm] = 'on'
        checked_realms = [r for r in realms if r in req.args]
        data['tag_realms'] = [{'name': realm,
                               'checked': realm in checked_realms}
                              for realm in realms]

        single_page = re.match(r"""(['"]?)(\w+)\1$""", query)
        if single_page:
            page_name = single_page.group(2)
            page = WikiPage(self.env, page_name)
            data['tag_page'] = page

        if query:
            data['tag_title'] = _("Showing objects matching '%s'") % query
        data['tag_query'] = query

        from tractags.macros import TagWikiMacros
        macros = TagWikiMacros(self.env)
        if not query:
            macro = 'TagCloud'
            query = '(%s) (%s)' % (' or '.join(['realm:' + \
                                                r for r in checked_realms]),
                                   query)
        else:
            macro = 'ListTagged'
            query += ',format=%s,cols=%s,realm=%s' % (self.default_format,
                                                      self.default_cols,
                                                      '|'.join(checked_realms))
        self.env.log.debug('Tag query: %s', query)
        try:
            # Query string without realm throws 'NotImplementedError'.
            data['tag_body'] = len(checked_realms) > 0 and \
                               macros.expand_macro(formatter, macro, query) \
                               or ''
        except InvalidQuery, e:
            data['tag_query_error'] = to_unicode(e)
            data['tag_body'] = macros.expand_macro(formatter, 'TagCloud', '')
        return 'tag_view.html', data, None

