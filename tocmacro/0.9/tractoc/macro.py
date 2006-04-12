# vim: expandtab tabstop=4

from trac.core import *
from trac.util import escape
from trac.wiki.formatter import Formatter, OutlineFormatter, wiki_to_oneliner, wiki_to_outline
from trac.wiki.api import IWikiMacroProvider, WikiSystem
from trac.wiki.model import WikiPage
from StringIO import StringIO
import os, re, string, inspect

__all__ = ['TracTocMacro']

class NullOut(object):
   def write(self, *args): pass


class MyOutlineFormatter(OutlineFormatter):

    def format(self, page, *args, **kwords):
        self.__page = page
        super(MyOutlineFormatter,self).format(*args, **kwords)

    def _heading_formatter(self, match, fullmatch):
        Formatter._heading_formatter(self, match, fullmatch)
        depth = min(len(fullmatch.group('hdepth')), 5)
        heading = match[depth + 1:len(match) - depth - 1]
        anchor = self._anchors[-1]
        text = wiki_to_oneliner(heading, self.env, self.db, self._absurls)
        text = re.sub(r'</?a(?: .*?)?>', '', text) # Strip out link tags
        self.outline.append((depth, '<a href="%s#%s">%s</a>' % (self.__page, anchor, text)))

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
    
    def get_macros(self):
        yield 'TOC'
        
    def get_macro_description(self, name):
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, args):
        db = self.env.get_db_cnx()
        formatter = MyOutlineFormatter(self.env)
        
        # If this is a page preview, try to figure out where its from
        current_page = req.hdf.getValue('wiki.page_name','WikiStart')
        in_preview = False
        if not req.hdf.has_key('wiki.page_name'):
            if req.path_info.startswith('/wiki/'):
                current_page = req.path_info[6:]
                in_preview = True
            else:
                return ''
         
        def get_page_text(pagename):
            """Return a tuple of (text, exists) for a page, taking into account previews."""
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
            elif arg.startswith('heading='):
                heading = arg[8:]
            elif arg.startswith('depth='):
                params['max_depth'] = int(arg[6:])
            elif arg.startswith('root='):
                root = arg[5:]
            else:
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
                prefix = (pagename.split('/'))[0]
                prefix = prefix.replace('\'', '\'\'')
                all_pages = list(WikiSystem(self.env).get_pages(prefix))
                if all_pages:
                    all_pages.sort()
                    out.write('<ol>')
                    for page in all_pages:
                        page_text, _ = get_page_text(page)
    
                        formatter.format(page, page_text, NullOut(), 1, 1)
                        header = ''
                        if formatter.outline:
                            title = formatter.outline[0][1]
                            title = re.sub('<[^>]*>','', title) # Strip all tags
                            header = ': ' + wiki_to_oneliner(title, self.env)
                        out.write('<li> <a href="%s">%s</a> %s</li>\n' % (self.env.href.wiki(page), page, header))
                    out.write('</ol>')        
                else :
                    out.write('<div class="system-message"><strong>Error: No page matching %s found</strong></div>' % prefix)
            else:
                page = root + pagename
                page_text, page_exists = get_page_text(page)
                if page_exists:
                    formatter.format(page, page_text, out, params['min_depth'], params['max_depth'])
                else:
                    out.write('<div class="system-message"><strong>Error: Page %s does not exist</strong></div>' % pagename)
        if not inline:
            out.write("</div>\n")
        return out.getvalue()

