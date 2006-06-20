# vim: expandtab tabstop=4

from trac.core import *
from trac.util import escape
from trac.wiki.formatter import Formatter, OutlineFormatter, wiki_to_oneliner, wiki_to_outline, system_message
from trac.wiki.api import WikiSystem
from trac.wiki.macros import WikiMacroBase 
from trac.wiki.model import WikiPage
from StringIO import StringIO
import os, re

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
    
    def render_macro(self, req, name, args):
        # Note for 0.11: `req` will be replaced by `formatter`
        #  req = formatter.req
        #  db = formatter.db
        db = self.env.get_db_cnx()
        formatter = MyOutlineFormatter(self.env) # FIXME 0.11: give 'req'
        
        # Bail out if we are in a no-float zone
        # Note for 0.11: if 'macro_no_float' in formatter.properties
        if 'macro_no_float' in req.hdf:
            return ''
        
        # If this is a page preview, try to figure out where its from
        # Note for 0.11: formatter.context could be the main `object`
        # to which the text being formatted belongs to...
        current_page = req.hdf['wiki.page_name']
        in_preview = req.args.has_key('preview')
         
        def get_page_text(pagename):
            """Return a tuple of (text, exists) for a page,
            taking into account previews.

            Note for 0.11: `formatter` should have the original text,
            so there would be no need for the `in_preview` stuff.
            """
            if in_preview and pagename == current_page:
                return (req.args.get('text',''), True)
            else:
                page = WikiPage(self.env,pagename)
                return (page.text, page.exists)            
                
        # Split the args
        if not args: args = ''
        args = [x.strip() for x in args.split(',')]
        # Options
        inline = False
        heading = 'Table of Contents'
        pagenames = []
        root = ''
        params = { 'title_index': False, 'min_depth': 1, 'max_depth': 6 }
        # Global options
        for arg in args:
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
            elif arg.startswith('heading='):
                heading = arg[8:]
            elif arg.startswith('depth='):
                params['max_depth'] = int(arg[6:])
            elif arg.startswith('root='):
                root = arg[5:]
            elif arg != '':
                pagenames.append(arg)
        
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
                li_class = pagename.startswith(current_page) and ' class="active"' or ''
                prefix = (pagename.split('/'))[0]
                prefix = prefix.replace('\'', '\'\'')
                all_pages = list(WikiSystem(self.env).get_pages(prefix))
                if all_pages:
                    all_pages.sort()
                    out.write('<ol>')
                    for page in all_pages:
                        page_text, _ = get_page_text(page)
    
                        formatter.format(current_page, page, page_text, NullOut(), 1, 1)
                        header = ''
                        if formatter.outline:
                            title = formatter.outline[0][1]
                            title = re.sub('<[^>]*>','', title) # Strip all tags
                            header = ': ' + wiki_to_oneliner(title, self.env)
                        out.write('<li%s> <a href="%s">%s</a> %s</li>\n' % (li_class, req.href.wiki(page), page, header))
                    out.write('</ol>')        
                else:
                    out.write(system_message('Error: No page matching %s found' % prefix))
            else:
                page = root + pagename
                page_text, page_exists = get_page_text(page)
                if page_exists:
                    formatter.format(current_page, page, page_text, out, params['min_depth'], params['max_depth'])
                else:
                    out.write(system_message('Error: Page %s does not exist' % pagename))
        if not inline:
            out.write("</div>\n")
        return out.getvalue()

