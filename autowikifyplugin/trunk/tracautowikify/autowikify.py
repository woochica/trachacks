import re
from trac.core import *
from trac.util import escape, Markup
from trac.wiki.api import WikiSystem, IWikiSyntaxProvider, IWikiChangeListener
try:
    set = set
except:
    from sets import Set as set


class AutoWikify(Component):
    """ Automatically create links for all known Wiki pages, even those that
    are not in CamelCase. """
    implements(IWikiSyntaxProvider, IWikiChangeListener)

    pages = set()
    pages_re = None

    def __init__(self):
        self._all_pages()
        self._update()

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        self.pages.add(page.name)
        self._update()

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        pass

    def wiki_page_deleted(self, page):
        if page.name in self.pages:
            self.pages.remove(page.name)
        else:
            self._all_pages()
        self._update()

    def wiki_page_version_deleted(self, page):
        pass

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        yield (self.pages_re, self._page_formatter)

    def get_link_resolvers(self):
        return []

    # Internal methods
    def _all_pages(self):
        self.pages = set(WikiSystem(self.env).get_pages())
        
    def _update(self):
        pattern = r'\b(?P<autowiki>' + '|'.join([p for p in self.pages if len(p) >= 3]) + r')\b'
        self.pages_re = pattern
        WikiSystem(self.env)._compiled_rules = None

    def _page_formatter(self, f, n, match):
        page = match.group('autowiki')
        return Markup('<a href="%s" class="wiki">%s</a>'
                      % (self.env.href.wiki(page),
                         escape(page)))
