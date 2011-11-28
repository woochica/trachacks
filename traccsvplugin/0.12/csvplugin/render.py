from trac.core import *
from trac.mimeview.api import Mimeview, IHTMLPreviewRenderer, content_to_unicode, is_binary
from genshi.builder import tag
from trac.web.chrome import add_stylesheet
import re

class CsvPluginRenderer(Component):
        
    implements(IHTMLPreviewRenderer)
    expand_tabs = False
    returns_source = False
    def get_quality_ratio(self, mimetype):
        self.log.debug("for mimetype: %s" % mimetype)
        if mimetype in ['text/comma-separated-values', 'text/csv']:
            return 8
        return 0

    def render(self, context, mimetype, content, filename=None, url=None):
        content = content.read()
        content = re.split('\r[\n]', content) 
        if not content:
            return None
        head = content[0]
        if not head:
            return None
        head = re.split(',', head)
        
        if not head:
            return None
        thead = tag.thead(tag.tr([tag.th(h) for h in head]))
        content = content[1:]
        if not content:
            return None
        tbody = []
        for r in content:
            if r:
                r = re.split(',', r)
                if r:
                    tbody.append(tag.tr([tag.td(c) for c in r ]))
        
        return tag.table(thead,tag.tbody(tbody), 
            class_="wiki")