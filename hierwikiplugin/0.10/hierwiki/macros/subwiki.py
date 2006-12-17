# Macros for the HierWiki plugin

from trac.core import *
from trac.wiki.api import WikiSystem
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
from trac.util.html import html

from StringIO import StringIO
import re, string, inspect

class SubWikiMacro(WikiMacroBase):
    """
    Inserts an alphabetic list of sub-wiki pages into the output.
    A sub-wiki page is a page that is is deeper in the hierachy than the current page.  e.g. if the current page is People, the this will return a list of all wiki entries that start with "People/"
    
    Accepts a prefix string as parameter: if provided, only pages with names that
    start with the prefix are included in the resulting list. If this parameter is
    omitted, all pages are listed.
    
    This now takes the text of the first heading and displays it as the link name.
    """

    TITLE_RE = re.compile(r'=+\s([^=]*)=+')

    def render_macro(self, req, name, args):
        # Args seperated by commas:
        # prefix,level
        #
        # Page Name prefix to search for.
        # how many 'levels' in the hierarchy to go down.
        prefix = req.hdf.getValue('wiki.page_name', '') + '/'
        level = 0
        if args:
            args = args.replace('\'', '\'\'')
            args = args.split(',')
            if args[0] != 'None':
                prefix = args[0]
            if len(args) > 1 and args[1] != 'None':
                level = int(args[1])

        pages = WikiSystem(self.env).get_pages(prefix)
        good_pages = []
        for p in pages:
            if level:
                len_name = p.split('/')
                if len(len_name) > level+1:
                    continue
            page = WikiPage(self.env, p)
            md = self.TITLE_RE.search(page.text)
            title = ''
            if md:
                title = md.group(1)
            good_pages.append((p, title))
        return html.UL([html.LI(html.A(p, title=t, href=req.href.wiki(p)), ' ', t) for p,t in good_pages])
        
