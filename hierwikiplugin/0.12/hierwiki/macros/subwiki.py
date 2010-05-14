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
    good_pages = []
    index = 0
    href = 0
    style = 1

    TITLE_RE = re.compile(r'=+\s([^=]*)=+')

    def expand_macro(self, formatter, name, args):
        # Args seperated by commas:
        # prefix,level
        #
        # Page Name prefix to search for.
        # how many 'levels' in the hierarchy to go down.
        
        prefix = formatter.resource.id + '/'
        self.log.debug('HierWikiPlugin: Generating SubWiki-Toc for %r', prefix)
                
        level = 0
        self.style = 1
        if args:
            args = args.replace('\'', '\'\'')
            args = args.split(',')
            if args[0] != None and args[0].strip() != '':
                prefix = args[0]
                
            if len(args) > 1 and args[1] != None and args[1].strip() != '':
                level = int(args[1])
                
            if len(args) > 2 and args[2] != None and args[2].strip() != '':
                self.style = int(args[2])

        if(prefix == '/'):
            prefix = ''

        pages = WikiSystem(self.env).get_pages(prefix)

        self.good_pages = []
        for p in pages:
            len_name = p.split('/')
            if level:
                if len(len_name) > level+1:
                    continue
            page = WikiPage(self.env, p)
            md = self.TITLE_RE.search(page.text)
            title = p
            if md:
                title = md.group(1)

            self.good_pages.append((p, title, len_name[len(len_name)-1]))
        
        self.good_pages.sort()
        self.href = formatter.context.href
        self.log.debug('HierWikiPlugin: Found %r valid pages below', len(self.good_pages))
        self.index = 0
        if len(self.good_pages) > 0:
            return self.render_tree(prefix, 1)
        else:
            return ''
        
    def render_tree(self, prefix, isroot):
        self.log.debug('HierWikiPlugin: Entering Recursion for %r at index %r of %r pages', prefix, self.index, len(self.good_pages))
        if self.index >= len(self.good_pages):
            return ''
        
        p = self.good_pages[self.index][0]
        
        if not p.startswith(prefix):
            return ' '
        
        buf = StringIO()
        if isroot:
            buf.write('<ul class="subwiki">')
        else:
            buf.write('<ul>')
        
        self.log.debug('HierWikiPlugin: Listing pages below')
        while self.index < len(self.good_pages):
            p = self.good_pages[self.index][0]
            t = self.good_pages[self.index][1]
            s = self.good_pages[self.index][2]
            
            if not p.startswith(prefix):
                break
            
            buf.write('<li>')

            if self.style == 0:
                x = p
                y = t
            elif self.style == 1:
                x = s
                y = t
            elif self.style == 2:
                x = t
                y = ''
            elif self.style == 3:
                x = p
                y = ''
            elif self.style == 4:
                x = s
                y = ''

            self.log.debug('HierWikiPlugin: Listing page %r', p)
            buf.write('<a href="' + self.href.wiki(p) + '" title="' + t + '">' + x + '</a> ' + y)
            self.index = self.index + 1
            if self.index >= len(self.good_pages):
                break
            
            buf.write(self.render_tree(p + '/', 0))
            buf.write('</li>')
        
        buf.write('</ul>')

        return buf.getvalue()
    
