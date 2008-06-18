"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

from trac.core import *
from trac.config import BoolOption
from trac.web.api import RequestDone
from trac.wiki.api import WikiSystem
from trac.wiki.formatter import wiki_to_html, Formatter, WikiProcessor
from trac.wiki.model import WikiPage
from trac.mimeview.api import Mimeview
from trac.util.text import shorten_line, to_unicode
from trac.util.html import Markup, escape

from tempfile import mkstemp
from StringIO import StringIO
import os
import re
import time
import urllib2
import base64

from api import IWikitoPDFFormat

EXCLUDE_RES = [
    re.compile(r'\[\[PageOutline([^]]*)\]\]'),
    re.compile(r'\[\[TracGuideToc([^]]*)\]\]'),
    re.compile(r'----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I)
]

class WikitoPDFOutput(Component):
    """Output wiki pages as a PDF/PS document using HTMLDOC."""
    
    implements(IWikitoPDFFormat)
        
    def wikitopdf_formats(self, req):
        yield 'pdf', 'PDF'
        yield 'ps', 'PS'
        
    def process_wikitopdf(self, req, format, title, subject, pages, version, date, pdfname):

        os.system("rm -f /tmp/tmp*wikitopdf")

	# Dump all pages to HTML files
	files = [self._page_to_file('', req, p) for p in pages]
        
        #Setup the title and license pages
        title_template = self.env.config.get('wikitopdf', 'titlefile')
        titlefile = self.get_titlepage(title_template, title, subject, date, version)
        
        # File to write PDF to
        pfile, pfilename = mkstemp('wikitopdf')
        os.close(pfile)       

	# Render
        os.environ["HTMLDOC_NOCGI"] = 'yes'
	codepage = self.env.config.get('trac', 'charset', 'iso-8859-1')

	htmldoc_format = {'pdf': 'pdf14', 'ps':'ps3'}[format]

	htmldoc_args = { 'book': None, 'format': htmldoc_format, 'titlefile': titlefile, 'charset': codepage }

	htmldoc_args.update(dict(self.env.config.options('wikitopdf-admin')))

        args_string = ' '.join(['--%s %s' % (arg, value or '') for arg, value
                                	in htmldoc_args.iteritems()])

	cmd_string = 'htmldoc %s %s -f %s'%(args_string, ' '.join(files), pfilename)

        self.log.info('WikitoPDF: Running %r', cmd_string)
        os.system(cmd_string.encode('latin-1'))
           
        out = open(pfilename, 'rb').read()
            
        # Clean up
        os.unlink(pfilename)
        for f in files:
            os.unlink(f)
              
        # Send the output
        req.send_response(200)
        req.send_header('Content-Type', {'pdf':'application/pdf', 'ps':'application/postscript'}[format])
        req.send_header('Content-Disposition', 'attachment; filename=' + pdfname + '.pdf')
        req.send_header('Content-Length', len(out))
        req.end_headers()
        req.write(out)
        raise RequestDone

    def _page_to_file(self, header, req, pagename, text=None):
        """Slight modification of some code from Alec's PageToPdf plugin."""

	hfile, hfilename = mkstemp('wikitopdf')
	codepage = self.env.config.get('trac', 'charset', 'iso-8859-1')

        base_dir = self.env.config.get('wikitopdf', 'base_dir')
        
        self.log.debug('WikitoPDF => Writting %s to %s using encoding %s', pagename, hfilename, codepage)

        page = text
        if text is None:
            text = WikiPage(self.env, pagename).text
            for r in EXCLUDE_RES:
                text = r.sub('', text)
	    page = wiki_to_html(text, self.env, req).encode(codepage, 'replace')

        imgpos = page.find('<img')
        while imgpos != -1:
                addrpos = page.find('src=', imgpos)
                base_dir = base_dir.encode('ascii')
                page = page[:addrpos+5] + base_dir + page[addrpos+5:]
                imgpos = page.find('<img', addrpos)

        page = page.replace('attachment', 'attachments')
        page = page.replace('?format=raw','')
        page = page.replace('<pre class="wiki">', '<table align="center" width="95%" border="1" bordercolor="#d7d7d7"><tr>'
						+ '<td bgcolor="#f7f7f7"><pre class="wiki">')
        page = page.replace('</pre>', '</pre></td></tr></table>')
        page = page.replace('<table class="wiki">', '<table class="wiki" border="1" width="100%">')

        self.log.debug('WikitoPDF => Page text is: %r', page)

	meta = ('<meta http-equiv="Content-Type" content="text/html; charset=%s"/>' % codepage).encode(codepage)
	os.write(hfile, '<html><head>' + meta + '</head><body>' + page + '</body></html>')
        os.close(hfile)
        return hfilename
	    
    def get_titlepage(self, template_path, title, subject, version, date):

	hfile, hfilename = mkstemp('wikitopdf')
	codepage = Mimeview(self.env).default_charset

	file_page = open(template_path, 'r')
	string_page = file_page.read()
	string_page = string_page.replace('#TITLE#', title)
	string_page = string_page.replace('#SUBJECT#', subject)
        string_page = string_page.replace('#VERSAO#', version)
        string_page = string_page.replace('#DATA#', date)
	os.write(hfile, string_page)
	os.close(hfile)
	return hfilename
	
