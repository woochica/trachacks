import re
from trac.core import *
from trac.util import escape, Markup, reversed, sorted
from trac.wiki.api import IWikiChangeListener, IWikiSyntaxProvider
from trac.wiki.model import WikiPage
from urlparse import urlparse

class Acronyms(Component):
    """ Automatically generates HTML acronyms from definitions in tables in a
    Wiki page (AcronymDefinitions by default).  """

    implements(IWikiSyntaxProvider, IWikiChangeListener)

    acronyms = {}
    compiled_acronyms = None
    valid_acronym = re.compile(r'^\S+$', re.UNICODE)
    acronym_page = property(lambda self: self.env.config.get('acronym', 'page',
                                                             'AcronymDefinitions'))
    def __init__(self):
        self._update_acronyms()

    def _update_acronyms(self):
        self.env.log.debug('Updating acronym database')
        page = WikiPage(self.env, self.acronym_page)
        self.acronyms = {}
        if not page.exists:
            return
        for line in page.text.splitlines():
            line = line.rstrip()
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
        print self.compiled_acronyms

        # XXX Very ugly, but only "reliable" way?
        from trac.wiki.parser import WikiParser
        WikiParser(self.env)._compiled_rules = None

    def _acronym_formatter(self, formatter, ns, match):
        acronym = match.group('acronym')
        selector = match.group('acronymselector')
        if acronym not in self.acronyms:
            return match.group(0)
        title, href, shref = self.acronyms[acronym]
        # Perform basic variable substitution
        title = title.replace('$1', selector).strip()
        suffix = ''
        if selector:
            if shref:
                href = shref.replace('$1', selector)
                acronym += ' ' + selector
            else:
                suffix = selector
        
        # if parsing the href string doesn't return a protocol string,
        # assume the href string is a reference to a wiki page        
        if href and not urlparse(href).scheme:
            href = self.env.href.wiki(href)            
                
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
