# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
# Copyright (C) 2011 Itamar Ostricher <itamarost@gmail.com>
# Copyright (C) 2011 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from genshi.builder import Markup, tag as builder

from trac.config import BoolOption, ListOption, Option
from trac.core import implements
from trac.resource import Resource, get_resource_description, \
                          get_resource_url, render_resource_link
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.util import embedded_numbers
from trac.util.compat import sorted, set
from trac.util.text import shorten_line, to_unicode
from trac.web.chrome import add_stylesheet
from trac.wiki.api import IWikiMacroProvider, parse_args

from tractags.api import TagSystem, _
from tractags.web_ui import TagTemplateProvider


# Check for unsupported pre-tags-0.6 macro keyword arguments.
_OBSOLETE_ARGS_RE = re.compile(r"""
    (expression|operation|showheadings|tagspace|tagspaces)=
    """, re.VERBOSE)


def render_cloud(env, req, cloud, renderer=None, caseless_sort=False):
    """Render a tag cloud

    :cloud: Dictionary of {object: count} representing the cloud.
    :param renderer: A callable with signature (tag, count, percent) used to
                     render the cloud objects.
    """
    min_px = 10.0
    max_px = 30.0
    scale = 1.0

    add_stylesheet(req, 'tags/css/tractags.css')

    if renderer is None:
        def default_renderer(tag, count, percent):
            href = get_resource_url(env, Resource('tag', tag), req.href)
            return builder.a(tag, rel='tag', title='%i' % count, href=href,
                             style='font-size: %ipx' %
                                   int(min_px + percent * (max_px - min_px)))
        renderer = default_renderer

    # A LUT from count to n/len(cloud)
    size_lut = dict([(c, float(i)) for i, c in
                     enumerate(sorted(set([r for r in cloud.values()])))])
    if size_lut:
        scale = 1.0 / len(size_lut)

    ul = builder.ul(class_='tagcloud')
    last = len(cloud) - 1
    if caseless_sort:
        # Preserve upper-case precedence within similar tags.
        items = reversed(sorted(cloud.iteritems(), key=lambda t: t[0].lower(),
                                reverse=True))
    else:
        items = sorted(cloud.iteritems())
    for i, (tag, count) in enumerate(items):
        percent = size_lut[count] * scale
        li = builder.li(renderer(tag, count, percent))
        if i == last:
            li(class_='last')
        li()
        ul(li, ' ')
    return ul


class TagWikiMacros(TagTemplateProvider):
    """Provides macros, that utilize the tagging system in wiki."""

    implements(IWikiMacroProvider)

    caseless_sort = BoolOption('tags', 'cloud_caseless_sort', default=False,
        doc="""Whether the tag cloud should be sorted case-sensitive.""")
    default_cols = Option('tags', 'listtagged_default_table_cols',
        'id|description|tags',
        doc="""Select columns and order for table format using a "|"-separated
            list of column names.

            Supported columns: realm, id, description, tags
            """)
    default_format = Option('tags', 'listtagged_default_format', 'oldlist',
        doc="""Set the default format for the handler of the `/tags` domain.

            || `oldlist` (default value) || The original format with a
            bulleted-list of "linked-id description (tags)" ||
            || `compact` || bulleted-list of "linked-description" ||
            || `table` || table... (see corresponding column option) ||
            """)
    exclude_realms = ListOption('tags', 'listtagged_exclude_realms', [],
        doc="""Comma-separated list of realms to exclude from tags queries
            by default, unless specifically included using "realm:realm-name"
            in a query.""")
    supported_cols = frozenset(['realm', 'id', 'description', 'tags'])

    def __init__(self):
        # TRANSLATOR: Keep macro doc style formatting here, please.
        self.doc_cloud = _("""Display a tag cloud.

    Show a tag cloud for all tags on resources matching query.

    Usage:

    {{{
    [[TagCloud(query)]]
    }}}

    See tags documentation for the query syntax.
    """)
        self.doc_listtagged = _("""List tagged resources.

    Usage:

    {{{
    [[ListTagged(query)]]
    }}}

    See tags documentation for the query syntax.
    """)

    # IWikiMacroProvider

    def get_macros(self):
        yield 'ListTagged'
        yield 'TagCloud'

    def get_macro_description(self, name):
        if name == 'ListTagged':
            return self.doc_listtagged
        elif name == 'TagCloud':
            return self.doc_cloud

    def expand_macro(self, formatter, name, content):
        if name == 'TagCloud':
            if not content:
                content = ''
            req = formatter.req
            all_tags = TagSystem(self.env).get_all_tags(req, content)
            return render_cloud(self.env, req, all_tags,
                                caseless_sort=self.caseless_sort)

        elif name == 'ListTagged':
            message = None
            req = formatter.req
            if _OBSOLETE_ARGS_RE.search(content):
                message = builder.div(builder.p(Markup(_("""
                    You seem to be using an old Tag query. Try using the
                    <a href="%(url)s">new syntax</a> in your
                    <strong>ListTagged</strong> macro.
                    """, url=req.href('tags')))),
                    class_='central system-message warning')
            args, kw = parse_args(content)
            cols = 'cols' in kw and kw['cols'] or self.default_cols
            format = 'format' in kw and kw['format'] or self.default_format
            query = args and args[0].strip() or None
            # Use TagsQuery arguments, if serving a web-UI call.
            realms = 'realm' in kw and kw['realm'].split('|') or None
            tag_system = TagSystem(self.env)
            all_realms = [p.get_taggable_realm()
                          for p in tag_system.tag_providers]
            if query and not realms:
                # First read query arguments (most likely wiki macro calls).
                for realm in all_realms:
                    if re.search('(^|\W)realm:%s(\W|$)' % (realm), query):
                        realms = realms and realms.append(realm) or [realm]
                if not realms:
                    # Apply ListTagged defaults to wiki macro call w/o realm.
                    realms = set(all_realms)-set(self.exclude_realms)
            if not realms:
                return ''
            query = '(%s) (%s)' % (query, ' or '.join(['realm:%s' % (r)
                                                       for r in realms]))
            self.env.log.debug('LISTTAGGED_QUERY: ' + query)
            query_result = tag_system.query(req, query)
            add_stylesheet(req, 'tags/css/tractags.css')

            def _link(resource):
                if resource.realm == 'ticket':
                    ticket = Ticket(self.env, resource.id)
                    return _ticket_anchor(ticket)
                else:
                    return render_resource_link(self.env, formatter.context,
                                                resource, 'compact')

            def _ticket_anchor(ticket):
                return builder.a('#%s' % ticket.id, class_=ticket['status'],
                                 href=formatter.href.ticket(ticket.id),
                                 title=shorten_line(ticket['summary']))

            if format == 'table':
                cols = [col for col in cols.split('|')
                        if col in self.supported_cols]
                # Use available translations from Trac core.
                try:
                    labels = TicketSystem(self.env).get_ticket_field_labels()
                except AttributeError:
                    # Trac 0.11 neither has the attribute nor uses i18n.
                    labels = {'id': 'Id', 'description': 'Description'}
                labels['realm'] = _('Realm')
                labels['tags'] = _('Tags')
                headers = [{'name': col,
                            'label': labels.get(col)}
                           for col in cols]
                container = builder.table(class_='wiki')
                thead = builder.thead()
                for col in cols:
                    for header in headers:
                        if header['name'] == col:
                            thead(builder.th(header['label']))
                container(thead)
            else:
                container = builder.ul(class_='taglist')
            for resource, tags in sorted(query_result, key=lambda r: \
                                         embedded_numbers(
                                         to_unicode(r[0].id))):
                desc = tag_system.describe_tagged_resource(req, resource)
                tags = sorted(tags)
                if tags:
                    rendered_tags = [_link(resource('tag', tag))
                                     for tag in tags]
                    if 'oldlist' == format:
                        item = builder.li(_link(resource), ' ', desc, ' (',
                                          rendered_tags[0],
                                          [(' ', tag)
                                           for tag in rendered_tags[1:]], ')'
                               )
                    else:
                        context=formatter.context
                        desc = desc or \
                               get_resource_description(self.env, resource,
                                                        context=context)
                        link = builder.a(desc,
                                         href=get_resource_url(self.env,
                                                               resource,
                                                               context.href)
                               )
                        if 'table' == format:
                            item = builder.tr()
                            for col in cols:
                                if col == 'id':
                                    item(builder.td(_link(resource)))
                                # Don't duplicate links to resource in both.
                                elif col == 'description' and 'id' in cols:
                                    item(builder.td(desc))
                                elif col == 'description':
                                    item(builder.td(link))
                                elif col == 'realm':
                                    item(builder.td(resource.realm))
                                elif col == 'tags':
                                    item(builder.td([(tag, ' ')
                                                 for tag in rendered_tags]))
                        else:
                            item = builder.li(link)
                else:
                    item = builder.li(_link(resource), ' ', desc)
                container(item)
            container = builder(message, container)
            return container

