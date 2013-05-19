# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
# Copyright (C) 2011-2013 Steffen Hoffmann <hoff.st@web.de>
# Copyright (C) 2011 Itamar Ostricher <itamarost@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re
import math

from genshi.builder import tag as builder
from trac.config import ListOption, Option
from trac.core import ExtensionPoint, implements
from trac.mimeview import Context
from trac.resource import Resource
from trac.util import to_unicode
from trac.util.text import CRLF
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor, \
                            add_stylesheet, add_ctxtnav
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage

from tractags.api import TagSystem, ITagProvider, _, tag_
from tractags.macros import TagTemplateProvider, TagWikiMacros, as_int
from tractags.query import InvalidQuery


class TagRequestHandler(TagTemplateProvider):
    """Implements the /tags handler."""

    implements(INavigationContributor, IRequestHandler)

    tag_providers = ExtensionPoint(ITagProvider)

    cloud_mincount = Option('tags', 'cloud_mincount', 1,
        doc="""Integer threshold to hide tags with smaller count.""")
    default_cols = Option('tags', 'default_table_cols', 'id|description|tags',
        doc="""Select columns and order for table format using a "|"-separated
            list of column names.

            Supported columns: realm, id, description, tags
            """)
    default_format = Option('tags', 'default_format', 'oldlist',
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

        match = re.match(r'/tags/?(.*)', req.path_info)
        tag_id = match.group(1) and match.group(1) or None
        query = req.args.get('q', '')

        realms = [p.get_taggable_realm() for p in self.tag_providers
                  if (not hasattr(p, 'check_permission') or \
                      p.check_permission(req.perm, 'view'))]
        if not (tag_id or query) or [r for r in realms if r in req.args] == []: 
            for realm in realms:
                if not realm in self.exclude_realms:
                    req.args[realm] = 'on'
        checked_realms = [r for r in realms if r in req.args]
        realm_args = dict(zip([r for r in checked_realms],
                              ['on' for r in checked_realms]))
        if tag_id and not re.match(r"""(['"]?)(\S+)\1$""", tag_id, re.UNICODE):
            # Convert complex, invalid tag ID's to query expression.
            req.redirect(req.href.tags(realm_args, q=tag_id))
        elif query:
            single_page = re.match(r"""(['"]?)(\S+)\1$""", query, re.UNICODE)
            if single_page:
                # Convert simple query for single tag ID.
                req.redirect(req.href.tags(single_page.group(2), realm_args))

        data = dict(page_title=_("Tags"), checked_realms=checked_realms)
        # Populate the TagsQuery form field.
        data['tag_query'] = tag_id and tag_id or query
        data['tag_realms'] = list(dict(name=realm,
                                       checked=realm in checked_realms)
                                  for realm in realms)
        if tag_id:
            page_name = tag_id
            page = WikiPage(self.env, page_name)
            data['tag_page'] = page

        macros = TagWikiMacros(self.env)
        if query or tag_id:
            # TRANSLATOR: The meta-nav link label.
            add_ctxtnav(req, _("Back to Cloud"), req.href.tags())
            macro = 'ListTagged'
            args = '%s,format=%s,cols=%s,realm=%s' \
                   % (tag_id and tag_id or query, self.default_format,
                      self.default_cols, '|'.join(checked_realms))
            data['mincount'] = None
        else:
            macro = 'TagCloud'
            mincount = as_int(req.args.get('mincount', None),
                              self.cloud_mincount)
            args = 'mincount=%s,realm=%s' % (mincount,
                                             '|'.join(checked_realms))
            data['mincount'] = mincount
        formatter = Formatter(self.env, Context.from_request(req,
                                                             Resource('tag')))
        self.env.log.debug('Tag macro arguments: %s', args)
        try:
            # Query string without realm throws 'NotImplementedError'.
            data['tag_body'] = len(checked_realms) > 0 and \
                               macros.expand_macro(formatter, macro, args) \
                               or ''
        except InvalidQuery, e:
            data['tag_query_error'] = to_unicode(e)
            data['tag_body'] = macros.expand_macro(formatter, 'TagCloud', '')
        add_stylesheet(req, 'tags/css/tractags.css')
        return 'tag_view.html', data, None
