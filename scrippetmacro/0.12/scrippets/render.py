# vim: expandtab
import re, time
from StringIO import StringIO

from genshi.builder import tag

from trac.core import *
from trac.wiki.formatter import format_to_html
from trac.util import TracError
from trac.util.text import to_unicode
from trac.web.chrome import add_stylesheet, ITemplateProvider
from trac.wiki.api import parse_args, IWikiMacroProvider
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule
from trac.mimeview.api import IContentConverter, IHTMLPreviewRenderer


import xml.etree.ElementTree as ElementTree
import xml.etree.cElementTree as cElementTree


class ScrippetRenderer(Component):
    implements(ITemplateProvider, IHTMLPreviewRenderer)

    ## IHTMLPreviewRenderer
    def get_quality_ratio(self, mimetype):
        self.log.debug("ScrippetRenderer quality for mimetype: %s" % mimetype)
        if mimetype == "text/fdx":
            return 9
        
    def render(self, context, mimetype, content, filename=None, url=None):
        add_stylesheet(context.req, 'scrippets/css/scrippets-full.css')                    
        if hasattr(content, 'read'):
            content = content.read()
        mode = "-full"
        theoutput = tag.div(class_="scrippet"+mode)
        fd_doc = cElementTree.fromstring(content)
        for fd_content in fd_doc.findall("Content"):
            for fd_paragraph in fd_content.findall("Paragraph"):
                ptype = fd_paragraph.get('Type')
                if ptype == "Action":
                    ptype = "action"
                elif ptype == "Character":
                    ptype = "character"
                elif ptype == "Dialogue":
                    ptype = "dialogue"
                elif ptype == "Parenthetical":
                    ptype = "parenthetical"
                elif ptype == "Scene Heading":
                    ptype = "sceneheader"
                elif ptype == "Transition":
                    ptype = "transition"
                else:
                    ptype = "action"
                #UNHANDLED FOR THE MOMENT
                #End Of Act
                #New Act
                #Shot
                #Show/Ep. Title
                #Teaser/Act One
                ptext = ""
                for fd_text in fd_paragraph.findall("Text"):
                    if fd_text.text != None:
                        ptext += fd_text.text
                if ptype in ["character","transition","sceneheader"]:
                    ptext = ptext.upper()
                theoutput += tag.p(ptext,class_=ptype+mode)
        return "%s" % theoutput
    
    ## ITemplateProvider
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('scrippets', resource_filename(__name__, 'htdocs'))]
                                      
    def get_templates_dirs(self):
        return []
