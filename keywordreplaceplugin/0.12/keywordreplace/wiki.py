import re
from trac.core import *
from trac.util import escape, Markup, reversed, sorted
from trac.wiki.api import IWikiChangeListener, IWikiSyntaxProvider
from trac.wiki.model import WikiPage
from urlparse import urlparse
from trac.wiki.formatter import format_to_oneliner
from trac.mimeview import Context

class KeywordReplace(Component):
    """ Replce wiki keywords from a table in a Wiki page. (KeywordReplace by default).  """

    implements(IWikiSyntaxProvider, IWikiChangeListener)

    replace = {}
    compiled_replace = None
    valid_replace = re.compile(r'^\S+$', re.UNICODE)
    replace_page = property(lambda self: self.env.config.get('replace', 'page',
                                                             'KeywordReplace'))
    def __init__(self):
        self._update_replace()

    def _update_replace(self):
        self.env.log.debug('Updating replace database')
        page = WikiPage(self.env, self.replace_page)
        self.replace = {}
        if not page.exists:
            return
        for line in page.text.splitlines():
            self.env.log.warning(line)
            line = line.rstrip()
            
            if line.startswith('||') and line.endswith('||') and line[3] != "'":               
                try:
                    a, d = ([i.strip() for i in line.strip('||').split('||')] + ['', ''])[0:2]
                    assert self.valid_replace.match(a), "Invalid replaces %s" % a
                    self.replace[a] = (escape(d))      
                except Exception, d:
                    self.env.log.warning("Invalid replaces line: %s", line)
        keys = reversed(sorted(self.replace.keys(), key=lambda a: len(a)))
        self.compiled_replace = \
            r'''\b(?P<replaces>%s)(?P<replacesselector>\w*)\b''' % '|'.join(keys)
        
        # XXX Very ugly, but only "reliable" way?
        from trac.wiki.parser import WikiParser
        WikiParser(self.env)._compiled_rules = None

    def _replaces_formatter(self, formatter, ns, match):
        replaces = match.group('replaces')
        selector = match.group('replacesselector')
        self.env.log.warning('formatter: %s ns: %s' % (formatter, ns))
        
        if replaces not in self.replace:
            return match.group(0)
        title = self.replace[replaces]
        # Perform basic variable substitution
        title = title.replace('$1', selector).strip()
        suffix = ''
        if selector:
            suffix = selector
        
        context = Context.from_request(formatter.req, formatter.resource)
        
        return Markup('<span>%s</span>' % (format_to_oneliner(self.env,context,title)))

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        if self.compiled_replace:
            yield (self.compiled_replace, self._replaces_formatter)

    def get_link_resolvers(self):
        return []

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        if page.name == self.replace_page:
            self._update_replace()

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        if page.name == self.replace_page:
            self._update_replace()

    def wiki_page_deleted(self, page):
        if page.name == self.replace_page:
            self._update_replace()

    def wiki_page_version_deleted(self, page):
        if page.name == self.replace_page:
            self._update_replace()
