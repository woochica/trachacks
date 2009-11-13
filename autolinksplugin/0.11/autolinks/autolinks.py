from trac.core import *
from trac.util.html import html
from trac.wiki.model import WikiPage
from trac.wiki.api import IWikiSyntaxProvider
from trac.wiki.api import WikiSystem

class AutoLinksModule(Component):

    implements(IWikiSyntaxProvider)

    def __init__(self):
        self.wikisys = WikiSystem(self.env)
    
    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        # copied and modified from trac/wiki/api.py
        from trac.wiki.formatter import Formatter
        wiki_page_name = (
            r"(([A-Z]+[a-z]{2,})|([A-Z]{3,}s?))"
            r"(?:#[\w:](?<!\d)(?:[\w:.-]*[\w-])?)?" # optional fragment id
            r"(?=:(?:\Z|\s)|[^:a-zA-Z]|\s|\Z)" # what should follow it
            )
        
        def wikipagename_link(formatter, match, fullmatch):
            return self._format_link(formatter, 'wiki', match, match)
        
        yield (r"!?(?<![/\-])\b" + wiki_page_name, wikipagename_link)

        
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

        if link:
            href = formatter.href.wiki(page) + fragment
            return html.A(label, href=href, class_='wiki')
        else:
            return label
            # use the following line instead to link pages even if a wiki page
            # by that name does not exist yet
            #return html.A(label+'?', href=href, class_='missing wiki', rel='nofollow')

