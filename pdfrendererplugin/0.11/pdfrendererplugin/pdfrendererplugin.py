"""
PdfRendererPlugin:
a plugin for Trac to render PDFs as HTML
http://trac.edgewall.org
"""

import subprocess

from trac.config import Option
from trac.core import *

from trac.mimeview.api import IHTMLPreviewRenderer

class PdfRendererPlugin(Component):

    implements(IHTMLPreviewRenderer)

    pdftotext = Option('attachment', 'pdftotext_path', 'pdftotext',
                       'path to pdftotext binary')

    ### methods for IHTMLPreviewRenderer

    """Extension point interface for components that add HTML renderers of
    specific content types to the `Mimeview` component.

    ----
    This interface will be merged with IContentConverter, as conversion
    to text/html will be simply a particular type of content conversion.

    However, note that the IHTMLPreviewRenderer will still be supported
    for a while through an adapter, whereas the IContentConverter interface
    itself will be changed.

    So if all you want to do is convert to HTML and don't feel like
    following the API changes, rather you should rather implement this
    interface for the time being.
    ---
    """

    def get_quality_ratio(self, mimetype):
        """Return the level of support this renderer provides for the `content`
        of the specified MIME type. The return value must be a number between
        0 and 9, where 0 means no support and 9 means "perfect" support.
        """
        if mimetype in ['application/pdf']:
            return 9
        return 0

    def render(self, context, mimetype, content, filename=None, url=None):
        """Render an XHTML preview of the raw `content` within a Context.

        The `content` might be:
         * a `str` object
         * an `unicode` string
         * any object with a `read` method, returning one of the above

        It is assumed that the content will correspond to the given `mimetype`.

        Besides the `content` value, the same content may eventually
        be available through the `filename` or `url` parameters.
        This is useful for renderers that embed objects, using <object> or
        <img> instead of including the content inline.
        
        Can return the generated XHTML text as a single string or as an
        iterable that yields strings. In the latter case, the list will
        be considered to correspond to lines of text in the original content.
        """        
        process = subprocess.Popen([self.pdftotext, content.name, '-'], stdout=subprocess.PIPE)
        output = process.communicate()[0]
        return '<textarea cols="80" rows="25" readonly>%s</textarea>' % output

        
