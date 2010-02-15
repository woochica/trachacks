"""
extendedcamelcase:
extend camelcase to link to wiki pages
Plugin for trac:  http://trac.edgewall.org
See also:  http://trac-hacks.org
"""


from trac.core import *
from trac.util.html import html
from trac.wiki.model import WikiPage
from trac.wiki.api import IWikiSyntaxProvider
from trac.wiki.api import WikiSystem

class extendedcamelcase(Component):

    implements(IWikiSyntaxProvider)

    def __init__(self):
        self.wikisys = WikiSystem(self.env)

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        # copied and modified from trac/wiki/api.py
        from trac.wiki.formatter import Formatter
        def wikipagename_link(formatter, match, fullmatch):
            return self._format_link(formatter, 'wiki', match, match)
        yield (r"(?P<name>\b([A-Z0-9]+[a-z0-9]*)+[A-Z0-9]+[a-z0-9]+\b)" , wikipagename_link)


    def get_link_resolvers(self):
        return []

    def _format_link(self, formatter, ns, page, label):
        # copied and modified from trac/wiki/api.py
        page, query, fragment = formatter.split_link(page)
        link = False
        if self.wikisys.has_page(page):
            link = True
        elif page[-1] == 's' and self.wikisys.has_page(page[:-1]):
            # if the page name ends in 's', see if there is a wiki page with the same name minus the 's'
            # if there is, it will be linked
            page = page[:-1]
            link = True
        href = formatter.href.wiki(page)+fragment
        if link:
            return html.A(label, href=href, class_='wiki')
        else:
            return html.A(label+'?', href=href, class_='missing wiki', rel='nofollow')

