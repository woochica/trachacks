"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
Modified by: Alvaro Iradier <alvaro.iradier@polartech.es>
"""

from trac.core import *
from trac.web.api import RequestDone
from trac.wiki.model import WikiPage
from api import IWikiPrintFormat
from wikiprint import wikipage_to_html, html_to_pdf, html_to_printhtml

class WikiPrintOutput(Component):
    """Output wiki pages as a PDF using PISA (xhtml2pdf) or Printable HTML."""
    
    implements(IWikiPrintFormat)
        
    def wikiprint_formats(self, req):
        yield 'pdfarticle', 'PDF Article'
        yield 'pdfbook', 'PDF Book'
        yield 'printhtml', 'HTML'
        
    def process_wikiprint(self, req, format, title, subject, pages, version, date, pdfname):

        # Dump all pages to HTML
        if format in ('pdfbook', 'pdfarticle'):
            fix_links = True
        else:
            fix_links = False            

        html_pages = [wikipage_to_html(WikiPage(self.env, p).text, p, self.env, req, fix_links) for p in pages]

        codepage = self.env.config.get('trac', 'default_charset', 'utf-8')

        # Send the output
        req.send_response(200)
        req.send_header('Content-Type', {
            'pdfbook': 'application/pdf',
            'pdfarticle': 'application/pdf',
            'printhtml':'text/html'}[format])

        if format == 'pdfbook':
            out = html_to_pdf(self.env, html_pages, codepage, book=True, title=title, subject=subject, version=version, date=date)
            req.send_header('Content-Disposition', 'attachment; filename=' + pdfname + '.pdf')
        elif format == 'pdfarticle':
            out = html_to_pdf(self.env, html_pages, codepage, book=False, title=title, subject=subject, version=version, date=date)
            req.send_header('Content-Disposition', 'attachment; filename=' + pdfname + '.pdf')
        elif format == 'printhtml':
            out = html_to_printhtml(self.env, html_pages, codepage, title=title, subject=subject, version=version, date=date)
        
        req.send_header('Content-Length', len(out))
        req.end_headers()
        req.write(out)
        raise RequestDone
    
    
