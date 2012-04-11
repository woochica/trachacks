"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

from tempfile import mkstemp
from trac.core import Component, implements
from trac.config import BoolOption
from trac.mimeview.api import Mimeview
from trac.web.api import RequestDone
from api import IWikiToPdfFormat
from wikitopdf import wiki_to_pdf, html_to_pdf

class WikiToPdfOutput(Component):
    """Output wiki pages as a PDF/PS document using HTMLDOC."""
    
    implements(IWikiToPdfFormat)
        
    def wikitopdf_formats(self, req):
        yield 'pdf' , 'PDF'
        yield 'ps'  , 'PS'
        yield 'html', 'HTML'
        
    def process_wikitopdf(self, req, format, title, subject, pages, version, date, pdfname):

        os.system("rm -f /tmp/tmp*wikitopdf")

        # Dump all pages to HTML files
        files = [self._page_to_file('', req, p) for p in pages]
        
        #Setup the title and license pages
        title_template = self.env.config.get('wikitopdf', 'pathtocover')
        if title_template == '':
                title_template = self.env.config.get('wikitopdf', 'titlefile')
        title_template = title_template + '/cover.html'
        titlefile = title_template and self.get_titlepage(title_template, title, subject, date, version) or None
        
        # Prepare html doc arguments
        codepage = self.env.config.get('trac', 'default_charset', 'iso-8859-1')

        oformat = { 'pdf':'pdf14', 'ps':'ps2', 'html':'html'}[format]
        htmldoc_args = { 'book': '', 'format': oformat, 'charset': codepage }
            
        if titlefile: htmldoc_args['titlefile'] = titlefile
        else: htmldoc_args['no-title'] = ''

        htmldoc_args.update(dict(self.env.config.options('wikitopdf-admin')))

        #render
        out = html_to_pdf(self.env, htmldoc_args, files, codepage)

        # Clean up
        if titlefile: os.unlink(titlefile)
        for f in files: os.unlink(f)
              
        # Send the output
        req.send_response(200)
        req.send_header('Content-Type', {'pdf':'application/pdf', 'ps':'application/postscript', 'html':'text/html'}[format])
        req.send_header('Content-Disposition', 'attachment; filename=' + pdfname + {'pdf':'.pdf', 'ps':'.ps', 'html': '.html'}[format])
        req.send_header('Content-Length', len(out))
        req.end_headers()
        req.write(out)
        raise RequestDone
    

    def _page_to_file(self, header, req, pagename):
        """Slight modification of some code from Alec's PageToPdf plugin."""

        # htmldoc doesn't support utf-8, we need to use some other input encoding
        codepage = self.env.config.get('trac', 'default_charset', 'iso-8859-1')
        base_dir = self.env.config.get('wikitopdf', 'base_dir')
        
        page = wiki_to_pdf(WikiPage(self.env, pagename).text, self.env, req, base_dir, codepage)
        
        hfile, hfilename = mkstemp('wikitopdf')
        self.log.debug('WikiToPdf => Writting %s to %s using encoding %s', pagename, hfilename, codepage)
        os.write(hfile, page)
        os.close(hfile)
        return hfilename
    
    
    def get_titlepage(self, template_path, title, subject, version, date):
        
        hfile, hfilename = mkstemp('wikitopdf')
        #codepage = Mimeview(self.env).default_charset
        string_page = ''
        
        try:
            file_page = open(template_path, 'r')
            string_page = file_page.read()
            string_page = string_page.replace('#TITLE#', title)
            string_page = string_page.replace('#SUBJECT#', subject)
            string_page = string_page.replace('#VERSION#', version)
            string_page = string_page.replace('#DATE#', date)
            
            title_template = self.env.config.get('wikitopdf', 'pathtocover')
            if title_template == '':
                title_template = self.env.config.get('wikitopdf', 'titlefile')
            string_page = string_page.replace('#PATHTOCOVER#',  title_template)
        except:
            os.close(hfile)
            return None
        
        os.write(hfile, string_page)
        os.close(hfile)
                
        return hfilename
    