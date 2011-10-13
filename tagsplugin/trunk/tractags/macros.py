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
from trac.util.presentation import Paginator
from trac.util.text import shorten_line, to_unicode
from trac.web.chrome import Chrome, add_link, add_stylesheet
from trac.wiki.api import IWikiMacroProvider, parse_args

from tractags.api import TagSystem, _
from tractags.web_ui import TagTemplateProvider

try:
    from trac.util  import as_int
except ImportError:
    def as_int(s, default, min=None, max=None):
        """Convert s to an int and limit it to the given range, or
        return default if unsuccessful (copied verbatim from Trac0.12dev)."""
        try:
            value = int(s)
        except (TypeError, ValueError):
            return default
        if min is not None and value < min:
            value = min
        if max is not None and value > max:
            value = max
        return value


# Check for unsupported pre-tags-0.6 macro keyword arguments.
_OBSOLETE_ARGS_RE = re.compile(r"""
    (expression|operation|showheadings|tagspace|tagspaces)=
    """, re.VERBOSE)


def render_cloud(env, req, cloud, renderer=None, caseless_sort=False,
                 mincount=None):
    """Render a tag cloud.

    :cloud: Dictionary of {object: count} representing the cloud.
    :param renderer: A callable with signature (tag, count, percent) used to
                     render the cloud objects.
    :param caseless_sort: Boolean, whether tag cloud should be sorted
                          case-sensitive.
    :param mincount: Integer threshold to hide tags with smaller count.
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

    if caseless_sort:
        # Preserve upper-case precedence within similar tags.
        items = reversed(sorted(cloud.iteritems(), key=lambda t: t[0].lower(),
                                reverse=True))
    else:
        items = sorted(cloud.iteritems())
    ul = li = None
    for i, (tag, count) in enumerate(items):
        percent = size_lut[count] * scale
        if mincount and count < as_int(mincount, 1):
            # Tag count is too low.
            continue
        if ul:
            # Found new tag for cloud; now add previously prepared one. 
            ul('\n', li)
        else:
            # Found first tag for cloud; now create the list.
            ul = builder.ul(class_='tagcloud')
        # Prepare current tag entry.
        li = builder.li(renderer(tag, count, percent))
    if li:
        # All tags checked; mark latest tag as last one (no tailing colon).
        li(class_='last')
        ul('\n', li, '\n')
    return ul and ul or _("No tags found")


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
    items_per_page = Option('tags', 'listtagged_items_per_page', 100,
        doc="""Number of tagged resources displayed per page in tag queries,
            by default""")
    items_per_page = as_int(items_per_page, 100)
    supported_cols = frozenset(['realm', 'id', 'description', 'tags'])

    def __init__(self):
        # TRANSLATOR: Keep macro doc style formatting here, please.
        self.doc_cloud = _("""Display a tag cloud.

    Show a tag cloud for all tags on resources matching query.

    Usage:

    {{{
    [[TagCloud(query,mincount=<n>)]]
    }}}
    mincount::
      Optional integer threshold to hide tags with smaller count.

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
        req = formatter.req
        if name == 'TagCloud':
            if not content:
                args = ''
            else:
                args, kw = parse_args(content)
            all_tags = TagSystem(self.env).get_all_tags(req, ' '.join(args))
            mincount = 'mincount' in kw and kw['mincount'] or None
            return render_cloud(self.env, req, all_tags,
                                caseless_sort=self.caseless_sort,
                                mincount=mincount)

        elif name == 'ListTagged':
            if _OBSOLETE_ARGS_RE.search(content):
                data = {'warning': 'obsolete_args'}
            else:
                data = {'warning': None}
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
            else:
                self.all_realms = all_realms
                self.query = query
                self.realms = list(realms)
            query = '(%s) (%s)' % (query, ' or '.join(['realm:%s' % (r)
                                                       for r in realms]))
            self.env.log.debug('LISTTAGGED_QUERY: ' + query)
            query_result = tag_system.query(req, query)

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
                    labels['id'] = _('Id')
                except AttributeError:
                    # Trac 0.11 neither has the attribute nor uses i18n.
                    labels = {'id': 'Id', 'description': 'Description'}
                labels['realm'] = _('Realm')
                labels['tags'] = _('Tags')
                self.env.log.debug(str(labels))
                headers = [{'label': labels.get(col)}
                           for col in cols]
                data.update({'cols': cols,
                             'headers': headers})

            results = sorted(query_result, key=lambda r: \
                             embedded_numbers(to_unicode(r[0].id)))
            results = self._paginate(req, results)
            rows = []
            for resource, tags in results:
                desc = tag_system.describe_tagged_resource(req, resource)
                tags = sorted(tags)
                if tags:
                    rendered_tags = [_link(resource('tag', tag))
                                     for tag in tags]
                    if 'oldlist' == format:
                        resource_link = _link(resource)
                    else:
                        context=formatter.context
                        desc = desc or \
                               get_resource_description(self.env, resource,
                                                        context=context)
                        resource_link = builder.a(desc, href=get_resource_url(
                                            self.env, resource, context.href))
                        if 'table' == format:
                            cells = []
                            for col in cols:
                                if col == 'id':
                                    cells.append(_link(resource))
                                # Don't duplicate links to resource in both.
                                elif col == 'description' and 'id' in cols:
                                    cells.append(desc)
                                elif col == 'description':
                                    cells.append(resource_link)
                                elif col == 'realm':
                                    cells.append(resource.realm)
                                elif col == 'tags':
                                    cells.append(
                                        builder([(tag, ' ')
                                                 for tag in rendered_tags]))
                            rows.append({'cells': cells})
                            continue
                rows.append({'desc': desc,
                             'rendered_tags': None,
                             'resource_link': _link(resource)})
            data.update({'format': format,
                         'paginator': results,
                         'results': rows,
                         'tags_url': req.href('tags')})

            # Work around a bug in trac/templates/layout.html, that causes a
            # TypeError for the wiki macro call, if we use add_link() alone.
            add_stylesheet(req, 'common/css/search.css')

            return Chrome(self.env).render_template(
                req, 'listtagged_results.html', data, 'text/html', True)

    def get_href(self, req, per_page=None, page=None):
        """Prepare href objects for pager links.

        Generate form-related arguments, strip arguments with default values.
        """
        form_realms = None
        if req.path_info == '/tags':
            form_realms = {}
            # Prepare realm arguments to keep form data consistent.
            for realm in self.realms:
                form_realms[realm] = 'on'
            realms = None
        elif set(self.realms) == set(self.all_realms):
            realms = None
        else:
            realms = self.realms
        if per_page == self.items_per_page:
            per_page = None
        if page == 1:
            page = None
        return req.href(req.path_info, form_realms, q=self.query,
                        realms=realms, listtagged_per_page=per_page,
                        listtagged_page=page)

    def _paginate(self, req, results):
        self.query = req.args.get('q', None)
        current_page = as_int(req.args.get('listtagged_page'), 1)
        items_per_page = as_int(req.args.get('listtagged_per_page'), None)
        if items_per_page is None:
            items_per_page = self.items_per_page
        result = Paginator(results, current_page - 1, items_per_page)

        pagedata = []
        shown_pages = result.get_shown_pages(21)
        for page in shown_pages:
            page_href = self.get_href(req, items_per_page, page)
            pagedata.append([page_href, None, str(page),
                             _("Page %(num)d", num=page)])

        attributes = ['href', 'class', 'string', 'title']
        result.shown_pages = [dict(zip(attributes, p)) for p in pagedata]

        result.current_page = {'href': None, 'class': 'current',
                               'string': str(result.page + 1), 'title': None}

        if result.has_next_page:
            next_href = self.get_href(req, items_per_page, current_page + 1)
            add_link(req, 'next', next_href, _('Next Page'))

        if result.has_previous_page:
            prev_href = self.get_href(req, items_per_page, current_page - 1)
            add_link(req, 'prev', prev_href, _('Previous Page'))
        return result

