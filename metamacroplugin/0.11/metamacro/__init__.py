from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem, parse_args
from trac.wiki.model import WikiPage
from trac.wiki.formatter import Formatter
from string import Template

from StringIO import StringIO

__all__ = ['ModelMacro']

class RelaxedIdTemplate(Template):
    idpattern = '[_a-z0-9]+'

class MetaMacro(Component):
    implements(IWikiMacroProvider)

    MACRO_PAGES = u'WikiMacros/'

    # IWikiMacroProvider methods
    def get_macros(self):
        for page in sorted(WikiSystem(self.env).get_pages(self.MACRO_PAGES)):
            yield page[len(self.MACRO_PAGES):]

    def get_macro_description(self, name):
        return u'Macro generated from %s%s page' % (self.MACRO_PAGES, name)

    def expand_macro(self, formatter, name, content):
        (args, kwargs) = parse_args(content, False)

        page_name = self.MACRO_PAGES + name
        page = WikiPage(self.env, page_name)
        if not page.exists:
            raise RuntimeError(u'Can\'t find page', page_name)

        for i, arg in enumerate(args):
            kwargs[unicode(i+1)] = arg

        text = RelaxedIdTemplate(page.text).safe_substitute(kwargs)

        out = StringIO()
        Formatter(self.env, formatter.context).format(text, out)

        out = out.getvalue().strip()
        if out.startswith(u'<p>'): out = out[3:]
        if out.endswith(u'</p>'): out = out[:-4]
        return out
