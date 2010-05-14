# Relative wiki link formatter
# Anti-cache code taken from Alec Thomas's AutoWikify plugin
from trac.core import *
from trac.web.api import IRequestFilter
from trac.wiki.api import WikiSystem, IWikiSyntaxProvider, IWikiChangeListener
from trac.wiki.model import WikiPage
from trac.util.html import html, escape

try:
    set = set
except:
    from sets import Set as set

__all__ = ['RelativeWikiFormatter']

def error(msg, *args):
    return html.DIV(html.P(msg%args), class_='system-message')

class RelativeWikiFormatter(Component):
    """Format links to pages relative to the current page."""
    
    implements(IWikiSyntaxProvider, IWikiChangeListener, IRequestFilter)

    def __init__(self):
        self._all_pages()
        self.pagebase = None
        self.pages_re = ''
        self._update('WikiStart')

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        self.log.debug('HierWikiPlugin: Adding syntax')
        yield self.pages_re, self._format_syntax
        
    def get_link_resolvers(self):
        yield 'relwiki', self._format_link
        yield 'rwiki', self._format_link
        
    # IWikiChangeListener methods (defeat the page cache)
    def wiki_page_added(self, page):
        self.pages.add(page.name)
        self.pagebase = None

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        pass

    def wiki_page_deleted(self, page):
        if page.name in self.pages:
            self.pages.remove(page.name)
        else:
            self._all_pages()
        self.pagebase = None

    def wiki_page_version_deleted(self, page):
        pass
        
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        self.log.debug('HierWikiPlugin: In pre-req filter')
        if req.path_info.startswith('/wiki'):
            self._update(req.args.get('page', 'WikiStart'))
        return handler
      
    def post_process_request(self, req, template, content_type):
        return template, content_type

    # Internal methods
    def _format_link(self, formatter, ns, target, label):
        if not formatter.req.path_info.startswith('/wiki'):
            return error('You can only use relative wiki links on wiki pages')
        if target.startswith('/'):
            return error('"%s" is not a relative path', target)
            
        pagename = formatter.req.args.get('page', 'WikiStart').split('/')[:-1]
        target = target.split('/')
        for val in target:
            if val == '.':
                continue
            elif val == '..':
                try:
                    del pagename[-1]
                except IndexError:
                    pass # XXX: What should be done here <NPK>
            else:
                pagename.append(val)
        dest = '/'.join(pagename)
        return formatter.wiki.link_resolvers['wiki'](formatter, 'wiki', dest, label)
        
    def _format_syntax(self, formatter, ns, match):
        page = match.group('relwiki')
        return html.A(escape(page), href=formatter.href.wiki(self.pagebase.rstrip('/'),page), class_='wiki')

    # More cache junk
    def _all_pages(self):
        self.pages = set(WikiSystem(self.env).get_pages())
        
    def _update(self, pagename):
        self.log.debug('HierWikiPlugin: Running an update')
        pagebase = '/'.join(pagename.split('/')[:-1])
        if pagebase != '':
            pagebase += '/'
        if pagebase != self.pagebase or self.pagebase is None:
            pages = set([p[len(pagebase):] for p in self.pages if p.startswith(pagebase)])
            pattern = r'\b(?P<relwiki>' + '|'.join(pages) + r')\b'
            self.log.debug('HierWikiPlugin: pagebase=%r pages=%r pattern=%r', pagebase, pages, pattern)
            self.pages_re = pattern
            self.pagebase = pagebase
            WikiSystem(self.env)._compiled_rules = None
