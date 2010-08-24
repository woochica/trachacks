from trac.core import *
from trac.wiki import IWikiSyntaxProvider
from trac.wiki.api import WikiSystem
from trac.config import BoolOption

class UnderscoreWiki(Component):
    implements(IWikiSyntaxProvider)
    ignore_missing_pages = BoolOption('underscore-wiki', 'ignore_missing_pages', 'false',
        """Enable/disable highlighting Under_Score_Wiki_Page links to missing pages""")
    uppercase_in_words = BoolOption('underscore-wiki', 'uppercase_in_words', 'false',
        """Enable/disable using upper case letters in places other than first character of every word (Foo_BAR, for example)""")
    def get_link_resolvers(self):
        pass
    def get_wiki_syntax(self):
        yield ( r"(?P<underscorewiki>%(word)s(?:_%(word)s)+)" % {'word': '[A-Z][a-z0-9%s]+' % (self.uppercase_in_words and 'A-Z' or '')}, self._format_regex\
_link)
    def _format_regex_link(self, formatter, ns, match):
        return WikiSystem(self.env)._format_link(formatter, ns, match.group('underscorewiki'), match.group('underscorewiki'), self.ignore_missing_pages)
