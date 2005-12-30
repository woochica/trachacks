
"""
Trac plugin to handle interwiki-style links.

@see: U{http://moinmoin.wikiwikiweb.de/InterWiki}
@see: U{http://projects.edgewall.com/trac/ticket/40}
"""

from trac.core import *
from trac.wiki.api import IWikiSyntaxProvider

class InterWikiLinkModule(Component):

    """
    Plug-in to handle InterWiki links within Trac.
    """

    implements(IWikiSyntaxProvider)

    INTERWIKI_CODEWORD = 'link'
    INTERWIKI_CONFIG_SECTION = 'interwiki'

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        """Return an iterable that provides additional wiki syntax."""
        return []

    def get_link_resolvers(self):
        """Return an iterable over (namespace, formatter) tuples."""
        yield (self.INTERWIKI_CODEWORD, self._format_link)

    # auxillary methods

    def _get_interwiki_map(self):
        options = self.config.options(self.INTERWIKI_CONFIG_SECTION)
        options = [(k.lower(), v) for k,v in options]
        return dict(options)

    def _format_link(self, formatter, ns, link, label):
        #print 'DEBUG: %s|%s|%s' % (ns, link, label)
        assert ns == self.INTERWIKI_CODEWORD
        interwikimap = self._get_interwiki_map()
        return format_interwiki_link(ns, link, label, interwikimap)

def format_interwiki_link(ns, link, label, interwikimap):
    """
    Formats TracLink into a InterWiki reference if appropriate.
    """
    def orig_repr(): # helper function 
        if label == (ns + ':' + link):
            return label
        else:
            return '[%s:%s %s]' % (ns, link, label)
    ids = link.split(':', 2)
    if len(ids) <> 2:
        return orig_repr()
    wikiname, pagename = ids
    if wikiname.lower() not in interwikimap:
        return orig_repr()
    url = interwikimap[wikiname.lower()] + pagename
    if label.startswith(ns + ':'):
        text = wikiname + ':' + pagename
    else:
        text = wikiname + ':' + label
    return '<a class="ext-link" href="%s"><span class="icon">' \
           '</span>%s</a>' % (url, text)

