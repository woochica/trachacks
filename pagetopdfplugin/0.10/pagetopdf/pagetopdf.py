from trac.core import *
from trac.util import escape
from trac.mimeview.api import IContentConverter
from trac.wiki.formatter import wiki_to_html
from tempfile import mkstemp
import os

class PageToPDFPlugin(Component):
    """Convert Wiki pages to PDF using HTMLDOC (http://www.htmldoc.org/)."""
    implements(IContentConverter)

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('pdf', 'PDF', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)

    def convert_content(self, req, input_type, source, output_type):
        hfile, hfilename = mkstemp('tracpdf')
        os.write(hfile, '<html><body>' + wiki_to_html(source, self.env, req).encode('utf-8') + '</body></html>')
        os.close(hfile)
        pfile, pfilename = mkstemp('tracpdf')
        os.close(pfile)
        os.system('export HTMLDOC_NOCGI="yes"; htmldoc --webpage --format pdf14 %s -f %s' % (hfilename, pfilename))
        out = open(pfilename).read()
        os.unlink(pfilename)
        os.unlink(hfilename)
        return (out, 'application/pdf')
