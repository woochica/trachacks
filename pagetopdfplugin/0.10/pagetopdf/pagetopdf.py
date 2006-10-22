from trac.core import *
from trac.util import escape
from trac.mimeview.api import IContentConverter
from trac.wiki.formatter import wiki_to_html
from tempfile import mkstemp
import os
import re

class PageToPDFPlugin(Component):
    """Convert Wiki pages to PDF using HTMLDOC (http://www.htmldoc.org/)."""
    implements(IContentConverter)

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('pdf', 'PDF', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)

    def convert_content(self, req, input_type, source, output_type):
        hfile, hfilename = mkstemp('tracpdf')
        codepage = self.env.config.get('trac', 'default_charset', 0)
        page = wiki_to_html(source, self.env, req).encode(codepage)
        page = re.sub('<img src="(?!\w+://)', '<img src="%s://%s' % (req.scheme, req.server_name), page)
        os.write(hfile, '<html><body>' + page + '</body></html>')
        os.close(hfile)
        pfile, pfilename = mkstemp('tracpdf')
        os.close(pfile)
        os.environ["HTMLDOC_NOCGI"] = 'yes'
        htmldoc_args = { 'webpage': None, 'format': 'pdf14', 'left': '1.5cm',
                         'right': '1.5cm', 'top': '1.5cm', 'bottom': '1.5cm',
                         'charset': codepage.replace('iso-', '')}
        htmldoc_args.update(dict(self.env.config.options('pagetopdf')))
        args_string = ' '.join(['--%s %s' % (arg, value or '') for arg, value
                                in htmldoc_args.iteritems()])
        self.env.log.debug(args_string)
        os.system('htmldoc %s %s -f %s' % (args_string, hfilename, pfilename))
        out = open(pfilename, 'rb').read()
        os.unlink(pfilename)
        os.unlink(hfilename)
        return (out, 'application/pdf')
