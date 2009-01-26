import re
from trac.core import *
from trac.wiki.api import IWikiSyntaxProvider, IWikiChangeListener
from trac.wiki.model import WikiPage
from trac.util import Markup, escape, sorted, reversed

class Acronyms(Component):
    """ Automatically generates HTML acronyms from definitions in tables in a
    Wiki page (AcronymDefinitions by default).  """

    implements(IWikiSyntaxProvider, IWikiChangeListener)

    acronyms = {}
    compiled_acronyms = None
    valid_acronym = re.compile('^\w+$')
    acronym_page = property(lambda self: self.env.config.get('acronym', 'page',
                                                          'AcronymDefinitions'))
    def __init__(self):
        self._update_acronyms()

    def _update_acronyms(self):
        page = WikiPage(self.env, self.acronym_page)
        self.env.log.debug('Updating acronym database')
        self.acronyms = {}
        if not page.exists:
            return
        for line in page.text.splitlines():
            if line.startswith('||') and line.endswith('||') and line[3] != "'":
                try:
                    a, d, u, s = ([i.strip() for i in line.strip('||').split('||')] + ['', ''])[0:4]
                    assert self.valid_acronym.match(a), "Invalid acronym %s" % a
                    self.acronyms[a] = (escape(d), escape(u), escape(s))
                except Exception, e:
                    self.env.log.warning("Invalid acronym line: %s (%s)", line, e)
        keys = reversed(sorted(self.acronyms.keys(), key=lambda a: len(a)))
        self.compiled_acronyms = \
            r'''\b(?P<acronym>%s)(?P<acronymselector>\w*)\b''' % '|'.join(keys)

        # XXX Very ugly, but only "reliable" way?
        from trac.wiki.parser import WikiParser
        WikiParser(self.env)._compiled_rules = None

    def _acronym_formatter(self, f, n, match):
        acronym = match.group('acronym')
        selector = match.group('acronymselector')
        if acronym not in self.acronyms:
            return match.group(0)
        title, href, shref = self.acronyms[acronym]
        # Perform basic variable subsitution
        title = title.replace('$1', selector).strip()
        suffix = ''
        if selector:
            if shref:
                href = shref.replace('$1', selector)
                acronym += ' ' + match.group('acronymselector')
            else:
                suffix = match.group('acronymselector')
                

        if href:
            return Markup('<a class="acronym" href="%s"><acronym title="%s">%s</acronym></a>%s'
                          % (href, title, acronym, suffix))
        else:
            return Markup('<acronym title="%s">%s</acronym>%s' % (title, acronym, suffix))

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        if self.compiled_acronyms:
            yield (self.compiled_acronyms, self._acronym_formatter)

    def get_link_resolvers(self):
        return []

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        if page.name == self.acronym_page:
            self._update_acronyms()

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        if page.name == self.acronym_page:
            self._update_acronyms()

    def wiki_page_deleted(self, page):
        if page.name == self.acronym_page:
            self._update_acronyms()

    def wiki_page_version_deleted(self, page):
        if page.name == self.acronym_page:
            self._update_acronyms()
