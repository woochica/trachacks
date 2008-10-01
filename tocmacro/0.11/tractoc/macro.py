# -*- coding: utf-8 -*-
import os
import re

from genshi.core import Markup
from genshi.builder import tag

from trac.core import *
from trac.resource import get_resource_url
from trac.util.compat import sorted
from trac.wiki.formatter import OutlineFormatter, system_message
from trac.wiki.api import WikiSystem, parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage


__all__ = ['TOCMacro']

class NullOut(object):
    def write(self, *args): pass


def outline_tree(env, ol, outline, context, active, min_depth, max_depth):
    if min_depth > max_depth:
        min_depth, max_depth = max_depth, min_depth
    max_depth = min(6, max_depth)
    min_depth = max(1, min_depth)
    previous_depth = min_depth
    
    stack = [None] * (max_depth + 1)
    # stack of (<element for new sublists>, <element for new items>)
    stack[previous_depth] = (None, ol)
    
    for depth, anchor, heading in outline:
        if min_depth <= depth <= max_depth:
            for d in range(previous_depth, depth):
                li, ol = stack[d]
                if not li:
                    li = tag.li()
                    ol.append(li)
                    stack[d] = (li, ol)
                new_ol = tag.ol()
                li.append(new_ol)
                stack[d+1] = (None, new_ol)
            href = get_resource_url(env, context.resource, context.href)
            if href.endswith(context.req.path_info):
                href = ''
            href += '#' + anchor
            li, ol = stack[depth]
            li = tag.li(tag.a(Markup(heading), href=href),
                        class_=active and 'active' or None)
            ol.append(li)
            stack[depth] = (li, ol)
            previous_depth = depth
    return stack[min_depth][0]


class TOCMacro(WikiMacroBase):
    """
    Generate a table of contents for the current page or a set of pages.
    If no arguments are given, a table of contents is generated for the
    current page, with the top-level title stripped: 
    {{{
        [[TOC]] 
    }}}
    To generate a table of contents for a set of pages, simply pass them
    as comma separated arguments to the TOC macro, e.g. as in
    {{{
    [[TOC(TracGuide, TracInstall, TracUpgrade, TracIni, TracAdmin, TracBackup,
          TracLogging, TracPermissions, TracWiki, WikiFormatting, TracBrowser,
          TracRoadmap, TracChangeset, TracTickets, TracReports, TracQuery,
          TracTimeline, TracRss, TracNotification)]]
    }}}
    A wildcard '*' can be used to fetch a sorted list of all pages starting with
    the preceding pagename stub:
    {{{
    [[TOC(Trac*, WikiFormatting, WikiMacros)]]
    }}}
    The following ''control'' arguments change the default behaviour of
    the TOC macro: 
    || '''Argument'''    || '''Meaning''' ||
    || {{{heading=<x>}}} || Override the default heading of "Table of Contents" ||
    || {{{noheading}}}   || Suppress display of the heading. ||
    || {{{depth=<n>}}}   || Display headings of ''subsequent'' pages to a maximum depth of '''<n>'''. ||
    || {{{inline}}}      || Display TOC inline rather than as a side-bar. ||
    || {{{sectionindex}}} || Only display the page name and title of each page in the wiki section. ||
    || {{{titleindex}}}  || Only display the page name and title of each page, similar to TitleIndex. ||
    || {{{notitle}}}     || Supress display of page title. ||
    For 'titleindex' argument, an empty pagelist will evaluate to all pages:
    {{{
    [[TOC(titleindex, notitle, heading=All pages)]]
    }}}
    'sectionindex' allows to generate a title index for all pages in a given section of the wiki.
    A section is defined by wiki page name, using '/' as a section level delimiter (like directories in a
    file system). Giving '/' or '*' as the page name produces the same result as 'titleindex' (title of all pages).
    If a page name ends with a '/', only children of this page will be processed. Else the page given in
    the argument is also included, if it exists. For 'sectionindex' argument, an empty pagelist will evaluate
    to all page below the same parent as the current page:
    {{{
    [[TOC(sectionindex, notitle, heading=This section pages)]]
    }}}

    """
    
    def expand_macro(self, formatter, name, args):
        context = formatter.context
        resource = formatter.context.resource
        
        # Bail out if we are in a no-float zone
        if hasattr(formatter, 'properties') and \
               'macro_no_float' in formatter.properties:
            return ''
        
        current_page = resource.id
         
        # Split the args
        args, kw = parse_args(args)
        # Options
        inline = False
        pagenames = []
        
        default_heading = 'Table of Contents'
        params = {'min_depth': 1, 'max_depth': 6}
        # Global options
        for arg in args:
            arg = arg.strip()
            if arg == 'inline':
                inline = True
            elif arg == 'noheading':
                default_heading = ''
            elif arg == 'notitle':
                params['min_depth'] = 2     # Skip page title
            elif (arg == 'titleindex') or (arg == 'sectionindex'):
                # sectionindex is a page-context sensitive titleindex
                if arg == 'sectionindex':
                    params['section_index'] = True
                params['title_index'] = True
                default_heading = default_heading and 'Page Index'
            elif arg == 'nofloat':
                return ''
            elif arg != '':
                pagenames.append(arg)
        heading = kw.pop('heading', '') or default_heading

        if 'depth' in kw:
           params['max_depth'] = int(kw['depth'])

        # Has the user supplied a list of pages?
        if not pagenames:
            # Be sure to test section_index first as title_index is also true in this case
            if 'section_index' in params:
                # Use 'parent' of current page (level delimiter is /), if any
                toks = re.match('^(?P<parent>.*)/[^/]*$',current_page)
                if toks:
                    pagenames.append(toks.group('parent')+'/')
                else:
                    pagenames.append('*')
            elif 'title_index' in params:
                pagenames.append('*')       # A marker for 'all'
            else:
                pagenames.append(current_page)
                params['root'] = ''
                params['min_depth'] = 2     # Skip page title
        # Check for wildcards and expand lists
        temp_pagenames = []
        for pagename in pagenames:
            if 'section_index' in params:
                # / is considered an equivalent to * in sectionindex
                if pagename == '/':
                    pagename = '*'
                if not pagename.endswith('*'):
                    pagename += '*'
            if pagename.endswith('*'):
                temp_pagenames.extend(sorted(
                        WikiSystem(self.env).get_pages(pagename[:-1])))
            else:
                temp_pagenames.append(pagename)
        pagenames = temp_pagenames

        base = tag.div(class_=inline and 'wiki-toc-inline' or 'wiki-toc')
        ol = tag.ol()
        base.append([heading and tag.h4(heading), ol])

        active = len(pagenames) > 1
        for pagename in pagenames:
            page_resource = resource(id=pagename)
            if not 'WIKI_VIEW' in context.perm(page_resource):
                # Not access to the page, so should not be included
                continue
            if 'title_index' in params:
                self._render_title_index(formatter, ol, page_resource,
                            active and pagename == current_page,
                            params['min_depth'] < 2)
            else:
                self._render_page_outline(formatter, ol, page_resource,
                                                        active, params)
        return base

    def get_page_text(self, formatter, page_resource):
        """Return a tuple of `(text, exists)` for the given page (resource)."""
        if page_resource.id == formatter.context.resource.id:
            return (formatter.source, True)
        else:
            page = WikiPage(self.env, page_resource)
            return (page.text, page.exists)

    def _render_title_index(self, formatter, ol, page_resource, active, show_title):
        page_text, page_exists = self.get_page_text(formatter, page_resource)
        if not page_exists:
            ol.append(system_message('Error: No page matching %s found' %
                                     page_resource.id))
            return
        ctx = formatter.context(page_resource)
        fmt = OutlineFormatter(self.env, ctx)
        fmt.format(page_text, NullOut())
        title = ''
        if show_title and fmt.outline:
            title = ': ' + fmt.outline[0][2]
        ol.append((tag.li(tag.a(page_resource.id,
                      href=get_resource_url(self.env, page_resource, ctx.href)),
                      Markup(title),
                      class_= active and 'active' or None)))

    def _render_page_outline(self, formatter, ol, page_resource, active, params):
        page = params.get('root', '') + page_resource.id
        page_text, page_exists = self.get_page_text(formatter, page_resource)
        if page_exists:
            ctx = formatter.context(page_resource)
            fmt = OutlineFormatter(self.env, ctx)
            fmt.format(page_text, NullOut())
            outline_tree(self.env, ol, fmt.outline, ctx,
                    active and page_resource.id == formatter.context.resource.id,
                    params['min_depth'], params['max_depth'])
        else:
            ol.append(system_message('Error: Page %s does not exist' %
                                     page_resource.id))
