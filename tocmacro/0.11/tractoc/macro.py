# -*- coding: utf-8 -*-
import os
import re
from StringIO import StringIO

from trac.core import *
from trac.wiki.formatter import Formatter, OutlineFormatter, system_message
from trac.wiki.api import WikiSystem, parse_args
from trac.wiki.macros import WikiMacroBase 


__all__ = ['TOCMacro']

class NullOut(object):
    def write(self, *args): pass


class MyOutlineFormatter(OutlineFormatter):

    def format(self, active_page, page, text, out, min_depth, max_depth):
        # XXX Code copied straight out of OutlineFormatter
        self.outline = []
        Formatter.format(self, text)

        active = ''
        if page == active_page:
            active = ' class="active"'

        if min_depth > max_depth:
            min_depth, max_depth = max_depth, min_depth
        max_depth = min(6, max_depth)
        min_depth = max(1, min_depth)

        curr_depth = min_depth - 1
        for depth, anchor, heading in self.outline:
            if depth < min_depth or depth > max_depth:
                continue
            if depth < curr_depth:
                out.write('</li></ol><li%s>' % active * (curr_depth - depth))
            elif depth > curr_depth:
                out.write('<ol><li%s>' % active * (depth - curr_depth))
            else:
                out.write("</li><li%s>\n" % active)
            curr_depth = depth
            out.write('<a href="%s#%s">%s</a>' %
                      (self.href.wiki(page), anchor, heading))
        out.write('</li></ol>' * curr_depth)


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
    The following ''control'' arguments change the default behaviour of
    the TOC macro: 
    || '''Argument'''    || '''Meaning''' ||
    || {{{heading=<x>}}} || Override the default heading of "Table of Contents" ||
    || {{{noheading}}}   || Suppress display of the heading. ||
    || {{{depth=<n>}}}   || Display headings of ''subsequent'' pages to a maximum depth of '''<n>'''. ||
    || {{{inline}}}      || Display TOC inline rather than as a side-bar. ||
    || {{{titleindex}}}  || Only display the page name and title of each page, similar to TitleIndex. ||
    
    Note that the current page must also be specified if individual wiki
    pages are given in the argument list.
    """
    
    def expand_macro(self, formatter, name, args):
        # Note for 0.11: `render_macro` will be replaced by `format_macro`...
        db = formatter.db
        context = formatter.context
        outlineformatter = MyOutlineFormatter(context)
        
        # Bail out if we are in a no-float zone
        if hasattr(formatter, 'properties') and \
               'macro_no_float' in formatter.properties:
            return ''
        
        current_page = context.id
         
        def get_page_text(pagename):
            """Return a tuple of `(text, exists)` for the given `pagename`."""
            if pagename == current_page:
                return (formatter.source, True)
            else:
                # TODO: after sandbox/security merge
                # page = context(id=pagename).resource
                from trac.wiki.model import WikiPage
                page = WikiPage(self.env, pagename, db=db)
                return (page.text, page.exists)
                
        # Split the args
        args, kw = parse_args(args)
        # Options
        inline = False
        pagenames = []
        heading = kw.pop('heading', 'Table of Contents')
        root = kw.pop('root', '')
        
        params = {'title_index': False, 'min_depth': 1, 'max_depth': 6}
        # Global options
        for arg in args:
            arg = arg.strip()
            if arg == 'inline':
                inline = True
            elif arg == 'noheading':
                heading = ''
            elif arg == 'notitle':
                params['min_depth'] = 2     # Skip page title
            elif arg == 'titleindex':
                params['title_index'] = True
                heading = ''
            elif arg == 'nofloat':
                return ''
            elif arg != '':
                pagenames.append(arg)

        if 'depth' in kw:
           params['max_depth'] = int(kw['depth'])

        # Has the user supplied a list of pages?
        if not pagenames:
            pagenames.append(current_page)
            root = ''
            params['min_depth'] = 2     # Skip page title

        out = StringIO()
        if not inline:
            out.write("<div class='wiki-toc'>\n")
        if heading:
            out.write("<h4>%s</h4>\n" % heading)
        for pagename in pagenames:
            if params['title_index']:
                li_class = pagename.startswith(current_page) and \
                           ' class="active"' or ''
                prefix = (pagename.split('/'))[0]
                prefix = prefix.replace('\'', '\'\'')
                all_pages = list(WikiSystem(self.env).get_pages(prefix))
                if all_pages:
                    all_pages.sort()
                    out.write('<ol>')
                    for page in all_pages:
                        page_text, _ = get_page_text(page)
    
                        outlineformatter.format(current_page, page, page_text,
                                                NullOut(), 1, 1)
                        header = ''
                        if outlineformatter.outline:
                            title = outlineformatter.outline[0][1]
                            title = re.sub('<[^>]*>','', title) # Strip all tags
                            header = ': ' + wiki_to_oneliner(title, self.env)
                        out.write('<li%s> <a href="%s">%s</a> %s</li>\n' %
                                  (li_class, context.href.wiki(page), page,
                                   header))
                    out.write('</ol>')
                else:
                    out.write(system_message('Error: No page matching %s '
                                             'found' % prefix))
            else:
                page = root + pagename
                page_text, page_exists = get_page_text(page)
                if page_exists:
                    outlineformatter.format(current_page, page, page_text, out,
                                            params['min_depth'],
                                            params['max_depth'])
                else:
                    print pagename, len(page_text)
                    out.write(system_message('Error: Page %s does not exist' %
                                             pagename))
        if not inline:
            out.write("</div>\n")
        return out.getvalue()
