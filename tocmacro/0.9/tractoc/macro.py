# vim: expandtab tabstop=4

from trac.core import *
from trac.util import escape
from trac.wiki.formatter import Formatter, wiki_to_oneliner
from trac.wiki.api import IWikiMacroProvider, WikiSystem
from trac.wiki.model import WikiPage
from StringIO import StringIO
import os, re, string, inspect

__all__ = ['TracTocMacro']

class TracTocMacro(Component):
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
    [[TOC(TracGuide, TracInstall, TracUpgrade, TracIni, TracAdmin, TracBackup, TracLogging,
             TracPermissions, TracWiki, WikiFormatting, TracBrowser, TracRoadmap, TracChangeset,
             TracTickets, TracReports, TracQuery, TracTimeline, TracRss, TracNotification)]]
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
    
    implements(IWikiMacroProvider)
    rules_re = re.compile(r"""(?P<heading>^\s*(?P<hdepth>=+)\s(?P<header>.*)\s(?P=hdepth)\s*$)""")
    
    def get_macros(self):
        yield 'TOC'
        
    def get_macro_description(self, name):
        return inspect.getdoc(self.__class__)

    def parse_toc(self, out, page, body, max_depth=999, min_depth=1, title_index=False):
        current_depth = min_depth
        in_pre = False
        first_li = True
        seen_anchors = []

        if title_index:
            min_depth = 1
            max_depth = 1

        for line in body.splitlines():

            # Skip over wiki-escaped code, e.g. code examples (Steven N.
            # Severinghaus <sns@severinghaus.org>)
            if in_pre:
                if line == '}}}':
                    in_pre = False
                else:
                    continue
            if line == '{{{':
                in_pre = True
                continue

            match = self.rules_re.match(line)
            if match:
                header = match.group('header')
                formatted_header = wiki_to_oneliner(header, self.env)
                new_depth = len(match.group('hdepth'))
                if new_depth < min_depth:
                    continue
                elif new_depth < current_depth:
                    while new_depth < current_depth:
                        current_depth -= 1
                        if current_depth < max_depth:
                            out.write("</ol>")
                    out.write("<li>")
                elif new_depth >= current_depth:
                    i = current_depth
                    while new_depth > i :
                        i += 1
                        if i <= max_depth:
                            out.write("<ol>")
                    if i <= max_depth:
                        out.write("<li>")
                    if first_li:
                        first_li = False
                    current_depth = new_depth
                if title_index:
                    out.write('<a href="%s">%s</a> : %s</li>\n' % (self.env.href.wiki(page), page, formatted_header))
                    break
                else:
                    default_anchor = Formatter._anchor_re.sub("", escape(header))
                    if not default_anchor:
                        continue
                    if default_anchor[0].isdigit():
                        default_anchor = 'a' + default_anchor
                    anchor = default_anchor
                    anchor_n = 1
                    while anchor in seen_anchors:
                        anchor = default_anchor + str(anchor_n)
                        anchor_n += 1
                    seen_anchors.append(anchor)
                    link = page
                    if current_depth <= max_depth:
                        out.write('<a href="%s#%s">%s</a></li>\n' % (self.env.href.wiki(link), anchor, formatted_header))
        while current_depth > min_depth:
            if current_depth <= max_depth:
                out.write("</ol>\n")
            current_depth -= 1

    def render_macro(self, req, name, args):
        db = self.env.get_db_cnx()
        
        # If this is a page preview, try to figure out where its from
        if not req.hdf.has_key('wiki.page_name'):
            md = re.match(self.env.href.wiki()+'/(.*)',req.path_info)
            if md:
                req.args.hdf['wiki.page_name'] = md.group(1)
            else:
                return ''
                
        # Split the args
        if not args: args = ''
        args = [x.strip() for x in args.split(',')]
        # Options
        inline = False
        heading_def = 'Table of Contents'
        heading = ''
        pagenames = []
        root = ''
        params = { }
        title_index = False
        # Global options
        for arg in args:
            if arg == 'inline':
                inline = True
            elif arg == 'noheading':
                heading = None
            elif arg == 'notitle':
                params['min_depth'] = 2     # Skip page title
            elif arg == 'titleindex':
                params['title_index'] = True
                heading_def = None
                title_index = True
            elif arg.startswith('heading='):
                heading = arg[8:]
            elif arg == '':
                continue
            elif arg.startswith('depth='):
                params['max_depth'] = int(arg[6:])
            elif arg.startswith('root='):
                root = arg[5:]
            else:
                pagenames.append(arg)
        
        # Has the user supplied a list of pages?
        if not pagenames:
            pagenames.append(req.hdf.getValue('wiki.page_name', 'WikiStart'))
            root = ''
            params['min_depth'] = 2     # Skip page title

        out = StringIO()
        if not inline:
            out.write("<div class='wiki-toc'>\n")
        if heading == '':
            heading = heading_def
        if heading:
            out.write("<h4>%s</h4>\n" % heading)
        out.write("<ol>\n")
        for pagename in pagenames:
            if title_index:
                prefix = (pagename.split('/'))[0]
                prefix = prefix.replace('\'', '\'\'')
                i = 0
                for page in WikiSystem(self.env).get_pages(prefix):
                    i += 1
                    page_text = WikiPage(self.env,page).text
                    self.parse_toc(out, page, page_text, **params)
                if i == 0:
                    out.write('<div class="system-message"><strong>Error: No page matching %s found</strong></div>' % prefix)
            else:
                pagename = root + pagename
                page = WikiPage(self.env,pagename)
                if page.exists:
                    self.parse_toc(out, pagename, page.text, **params)
                else:
                    out.write('<div class="system-message"><strong>Error: Page %s does not exist</strong></div>' % pagename)
        out.write("</ol>\n")
        if not inline:
            out.write("</div>\n")
        return out.getvalue()
