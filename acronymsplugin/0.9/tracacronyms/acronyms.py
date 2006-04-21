import re
from trac.core import *
from trac.wiki.api import IWikiSyntaxProvider, IWikiChangeListener
from trac.wiki.model import WikiPage
from trac.util import Markup, escape

class Acronyms(Component):
    """ Automatically generates HTML acronyms from definitions in tables in a
    Wiki page (AcronymDefinitions by default).
    
    Acronyms are in the form `<acronym>[<id>]` and are defined in a table with
    four columns:
    
        `Acronym, Description [, URL [, ID URL]]`

    Only the first two columns are required.
    
    If an `<id>` is provided, the ID URL is used and any occurrences of the symbol
    `$1` in the description and the ID URL are substituted with the `<id>`.

    Rows starting with `||'` are ignored.

    eg. The following acronym definition table:

    {{{
    ||'''Acronym'''||'''Description'''||'''URL'''||'''ID URL'''||
    ||RFC||Request For Comment $1||http://www.ietf.org/rfc.html||http://www.ietf.org/rfc/rfc$1.txt||
    }}}

    Has the following effect:
    
    `RFC` becomes
    {{{
        <a href="http://www.ietf.org/rfc.html">
         <acronym title="Request For Comment">
          RFC
         </acronym>
        </a>
    }}}

    `RFC2315` becomes
    {{{
        <a href="http://www.ietf.org/rfc/rfc2315.txt">
         <acronym title="Request For Comment 2315">
          RFC 2315
         </acronym>
        </a>
    }}}
    """

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
                    self.acronyms[a] = (d, u, s)
                except Exception, e:
                    self.env.log.warning("Invalid acronym line: %s (%s)", line, e)
        keys = self.acronyms.keys()
        keys.sort(cmp=lambda a, b: -cmp(len(a), len(b)))
        self.compiled_acronyms = \
            r'''\b(?P<acronym>%s)(?P<acronymselector>\w*)\b''' % '|'.join(keys)

    def _acronym_formatter(self, f, n, match):
        acronym = match.group('acronym')
        selector = match.group('acronymselector')
        if acronym not in self.acronyms:
            return match.group(0)
        title, href, shref = self.acronyms[acronym]
        # Perform basic variable subsitution
        title = title.replace('$1', selector).strip()
        if selector:
            if shref:
                href = shref.replace('$1', selector)
            acronym += ' ' + match.group('acronymselector')

        href, title, acronym = escape(href), escape(title), escape(acronym)
        if href:
            return Markup('<a class="acronym" href="%s"><acronym title="%s">%s</acronym></a>' 
                          % (href, title, acronym))
        else:
            return Markup('<acronym title="%s">%s</acronym>' % (title, acronym))

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
