import re
from trac.core import *
from genshi.builder import tag
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.wiki.macros import WikiMacroBase

EMBED_COUNT = '_togglemacro_embed_count'

class ToggleMacro(WikiMacroBase):
    """
    """
    implements(ITemplateProvider)

    def get_macros(self):
        """Return a list of provided macros"""
        yield 'Toggle'

    def get_macro_description(self, name):
        return '''desc'''

    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content, strict=True)
        if len(args) >= 1:
            arg = args[0]
        elif len(args) == 0:
            raise TracError('Toggle block is not defined')

        add_script(formatter.req, 'togglemacro/js/togglemacro.js')
        add_stylesheet(formatter.req, 'togglemacro/css/togglemacro.css')
        
        embed_count = getattr(formatter, EMBED_COUNT, 0)
        embed_count += 1
        setattr(formatter, EMBED_COUNT, embed_count)
        
        tags = []
        
        if arg == "begin":
            tags.append('<div class="toggle_container">')
        elif arg == "end":
            tags.append("</div>")

        return ''.join([str(i) for i in tags])

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('togglemacro', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

