from trac.core import *
from trac.web.api import RequestDone
from trac.wiki.api import WikiSystem
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage
from trac.mimeview.api import Mimeview

from tempfile import mkstemp
import os
import re

from api import ICombineWikiFormat

EXCLUDE_RES = [
    re.compile('\[\[PageOutline([^]]*)\]\]'),
    re.compile('----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I)
]

class PDFOutputFormat(Component):
    """Output combined wiki pages as a PDF using HTMLDOC."""
    
    implements(ICombineWikiFormat)
        
    TITLE_HTML = u"""
    <table><tr><td height="100%%" width="100%%" align="center" valign="middle">
    <h1>%s</h1>
    </td></tr></table>
    """

    def combinewiki_formats(self, req):
        yield 'pdf', 'PDF'
        
    def process_combinewiki(self, req, format, title, pages):
        # Dump all pages to HTML files
        files = [self._page_to_file(req, p) for p in pages]
        titlefile = self._page_to_file(req, title, self.TITLE_HTML%title)
            
        # File to write PDF to
        pfile, pfilename = mkstemp('tracpdf')
        os.close(pfile)       
         
        # Render
        os.environ["HTMLDOC_NOCGI"] = 'yes'
        codepage = Mimeview(self.env).default_charset
        htmldoc_args = { 'book': None, 'format': 'pdf14', 'left': '1.5cm',
                         'right': '1.5cm', 'top': '1.5cm', 'bottom': '1.5cm',
                         'charset': codepage.replace('iso-', ''), 'title': None,
                         'titlefile': titlefile}
        htmldoc_args.update(dict(self.env.config.options('pagetopdf')))
        htmldoc_args.update(dict(self.env.config.options('combinewiki')))
        args_string = ' '.join(['--%s %s' % (arg, value or '') for arg, value
                                in htmldoc_args.iteritems()])
        cmd_string = 'htmldoc %s %s -f %s'%(args_string, ' '.join(files), pfilename)
        self.log.info('CombineWikiModule: Running %r', cmd_string)
        os.system(cmd_string)
            
        out = open(pfilename, 'rb').read()
            
        # Clean up
        os.unlink(pfilename)
        for f in files:
            os.unlink(f)
        os.unlink(titlefile)
              
        # Send the output
        req.send_response(200)
        req.send_header('Content-Type', 'application/pdf')
        req.send_header('Content-Length', len(out))
        req.end_headers()
        req.write(out)
        raise RequestDone

    def _page_to_file(self, req, pagename, text=None):
        """Slight modification of some code from Alec's PageToPdf plugin."""
        hfile, hfilename = mkstemp('tracpdf')
        codepage = Mimeview(self.env).default_charset

        self.log.debug('CombineWikiModule: Writting %s to %s using encoding %s', pagename, hfilename, codepage)

        page = text
        if text is None:
            text = WikiPage(self.env, pagename).text
            for r in EXCLUDE_RES:
                text = r.sub('', text)
            page = wiki_to_html(text, self.env, req).encode(codepage)
        self.log.debug('CombineWikiModule: Page text is %r', page)

        page = re.sub('<img src="(?!\w+://)', '<img src="%s://%s:%d' % (req.scheme, req.server_name, req.server_port), page)
        os.write(hfile, '<html><head><title>' + pagename.encode(codepage) + '</title></head><body>' + page + '</body></html>')
        os.close(hfile)
        return hfilename


class TiddlyWikiOutputFormat(Component):
    """Output combined wiki pages as a TiddlyWiki."""
    
    implements(ICombineWikiFormat)
    
    def combinewiki_formats(self, req):
        yield 'tiddlywiki', 'TiddlyWiki'
        
    def process_combinewiki(self, req, format, title, pages):
        pass
