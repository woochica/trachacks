import re

from trac.core import *
from trac.util.html import html
from trac.wiki import IWikiSyntaxProvider
from trac.wiki import WikiSystem
from trac.wiki import WikiPage

class TermLink(Component):
    implements(IWikiSyntaxProvider)

    _term_ns = "term"
    _wiki_prefix = "Term/"
    _desc_regex = re.compile(r"^= (.+) =$")

    def _term_desc(self, target):
        page = self._wiki_prefix + target
        content = WikiPage(self.env, page).text
        lines = content.splitlines()
        if len(lines) <= 0:
            return target
        m = self._desc_regex.match(lines[0])
        if m:
            return m.group(1)
        else:
            return self._term_ns + ":" + target

    def _format_term(self, formatter, ns, target, label):
        wiki = WikiSystem(self.env)
        page = self._wiki_prefix + target
        href = formatter.href.wiki(page)
        if wiki.has_page(page):
            return html.A(wiki.format_page_name(self._term_desc(target)),
                        href=href)
        else:
            return html.A(wiki.format_page_name(self._term_ns + ":" + target)
                            + "?",
                            href=href, class_="missing wiki", rel="nofollow")

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        return []
    def get_link_resolvers(self):
        yield (self._term_ns, self._format_term)
