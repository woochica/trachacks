
from trac.core import *
from trac.wiki import IWikiSyntaxProvider
from trac.util.html import html


class ExtLinkRewriterProvider(Component):
    """Rewrite External Link URL
    """
    implements(IWikiSyntaxProvider)
    
    _rewrite_format = "http://del.icio.us/url?url=%s"
    _rewrite_namespaces = "http,https,ftp"
    _rewrite_target = ""
    
    def get_wiki_syntax(self):
        """IWikiSyntaxProvider#get_wiki_syntax
        """
        return []
    
    def get_link_resolvers(self):
        """IWikiSyntaxProvider#get_link_resolvers
        """
        self._load_config()
        return [(ns.strip(), self._link_formatter)
                for ns in self._rewrite_namespaces.split(",")]
    
    def _link_formatter(self, formatter, ns, target, label):
        try:
            newtarget = self._rewrite_format % (ns + ":" + target,)
        except:
            newtarget = ns + ":" + target
            msg = "ExtLinkRewriter Plugin format error: %s"
            msg %= (self._rewrite_format,)
            self.log.error(msg)
            pass
        return self._make_ext_link(formatter, newtarget, label,
                                   self._rewrite_target)
    
    def _make_ext_link(self, formatter, url, text, target=""):
        """Formatter._make_ext_link with target attr
        """
        if not url.startswith(formatter._local):
            return html.A(html.SPAN(text, class_="icon"),
                          class_="ext-link", href=url, target=target or None)
        else:
            return html.A(text, href=url, target=target or None)
        pass
    
    def _load_config(self):
        self._update_config("format")
        self._update_config("namespaces")
        self._update_config("target")
        pass
    
    def _update_config(self, key):
        attrname = "_rewrite_" + key
        oldval = getattr(self, attrname)
        newval = self.config.get("extlinkrewriter", key, oldval)
        setattr(self, attrname, newval)
        pass
    pass
