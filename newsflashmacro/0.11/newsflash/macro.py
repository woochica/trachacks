from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase
from genshi import Markup
from genshi.builder import tag
from pkg_resources import resource_filename

class NewsFlashMacro(WikiMacroBase):
    """Makes a colored box from the contents of the macro."""
    
    implements(ITemplateProvider)
    
    # ITemplateProvider
    def get_templates_dirs(self):
        return []
        
    def get_htdocs_dirs(self):
        yield 'newsflash', resource_filename(__name__, 'htdocs')

    # IWikiMacroProvier methods
    def expand_macro(self, formatter, name, content):
        add_stylesheet(formatter.req, 'newsflash/css/newsflash.css')
        return tag.div(format_to_html(self.env, formatter.context, content),
                       class_='newsflash')


class NewsFlashStartMacro(WikiMacroBase):
    """Start a newflash box."""
    
    def expand_macro(self, formatter, name, content):
        add_stylesheet(formatter.req, 'newsflash/css/newsflash.css')
        return Markup('<div class="newsflash">')


class NewsFlashEndMacro(WikiMacroBase):
    """End a newflash box."""
    
    def expand_macro(self, formatter, name, content):
        return Markup('</div>')


