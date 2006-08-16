from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html

import inspect

__all__ = ['NewsFlashMacro', 'NewsFlashStartMacro', 'NewsFlashEndMacro']

class WikiMacroBase(Component):
    """Abstract base class for wiki macros."""

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        name = self.__class__.__name__
        if name.endswith('Macro'):
            name = name[:-5]
        yield name

    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, content):
        raise NotImplementedError

class NewsFlashMacro(WikiMacroBase):
    """Makes a colored box from the contents of the macro."""
    
    implements(ITemplateProvider, IWikiMacroProvider)
    
    # ITemplateProvider
    def get_templates_dirs(self):
        return []
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('newsflash', resource_filename(__name__, 'htdocs'))]

    # IWikiMacroProvier methods
    def render_macro(self, req, name, content):
        add_stylesheet(req, 'newsflash/css/newsflash.css')
        return '<div class="newsflash">%s</div>'%wiki_to_html(content, self.env, req)

class NewsFlashStartMacro(WikiMacroBase):
    """Start a newflash box."""
    
    implements(IWikiMacroProvider)
    
    def render_macro(self, req, name, content):
        add_stylesheet(req, 'newsflash/css/newsflash.css')
        return '<div class="newsflash">'

class NewsFlashEndMacro(WikiMacroBase):
    """End a newflash box."""
    
    implements(IWikiMacroProvider)
    
    def render_macro(self, req, name, content):
        return '</div>'
        
        
