# -*- coding: utf-8 -*-

from genshi.builder import tag
from trac.core import *
from trac.mimeview.api import IHTMLPreviewAnnotator, Mimeview
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.api import IWikiMacroProvider

import inspect
import re


_processor_re = re.compile('#\!([\w+-][\w+-/]*)')

class LinenoMacro(Component):
    """Prints line numbered code listings"""
    
    implements(IWikiMacroProvider, ITemplateProvider)
    
    # IWikiMacroProvider
    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        """Yield the name of the macro based on the class name."""
        name = self.__class__.__name__
        if name.endswith('Macro'):
            name = name[:-5]
        yield name

    def get_macro_description(self, name):
        """Return a plain text description of the macro with the specified name.
        """
        return inspect.getdoc(self.__class__)
    
    # ITemplateProvider
    def get_templates_dirs(self):
        return []
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('lineno', resource_filename(__name__, 'htdocs'))]
    
    def expand_macro(self, formatter, name, content):
        add_stylesheet(formatter.req, 'lineno/css/lineno.css')
        mt = 'txt'
        match = _processor_re.search(content)
        if match:
            mt = match.group().strip()[2:]
            content = content[match.end():]
        
        mimetype = Mimeview(formatter.env).get_mimetype(mt)
        if not mimetype:
            mimetype = Mimeview(formatter.env).get_mimetype('txt')
        
        annotations = ['linenomacro']
        return Mimeview(self.env).render(formatter.context,
                                         mimetype, content, None, None, annotations)

class LinenoAnnotator(Component):
    
    implements(IHTMLPreviewAnnotator)
    
    def get_annotation_type(self):
        return 'linenomacro', 'Line', 'Line numbers'

    def get_annotation_data(self, context):
        return None

    def annotate_row(self, context, row, lineno, line, data):
        row.append(tag.th(id='L%s' % lineno)(
            lineno
        ))
