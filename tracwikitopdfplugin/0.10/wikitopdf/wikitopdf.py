"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

from trac.core import *
from trac.util import escape
from trac.mimeview.api import IContentConverter
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage
from tempfile import mkstemp
import os
import re

EXCLUDE_RES = [
        re.compile(r'\[\[PageOutline([^]]*)\]\]'),
        re.compile(r'\[\[TracGuideToc([^]]*)\]\]'),
        re.compile(r'\[\[TOC([^]]*)\]\]'),
        re.compile(r'----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I)
]

class WikitoPDFPage(Component):
    """Convert Wiki pages to PDF using HTMLDOC (http://www.htmldoc.org/)."""
    implements(IContentConverter)

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('pdf', 'WikitoPDF', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)

    def convert_content(self, req, input_type, text, output_type):

        os.system("rm -f /tmp/tmp*wikitopdf")
        os.environ["HTMLDOC_NOCGI"] = 'yes'
        codepage = self.env.config.get('trac', 'charset', 'iso-8859-1')

        # File to write PDF to
        pfile, pfilename = mkstemp('wikitopdf')
        os.close(pfile)       
        #return (text, 'text/plain') 

        mo = None
        if text.startswith('----'):
        
                mo = re.match(r'\-+\r\n([^\-].*?)\r\n\-\-\-\-+\r\n(.*)', text, re.DOTALL | re.MULTILINE)
                
        if mo:
                titletext = mo.group(1)
                pagenames = [p for p in re.findall(r'\[wiki:([^\] ]+)', mo.group(2))]
                toctitle = re.search(r'^=+\s*([^=]*?)\s*=', mo.group(2), re.MULTILINE)

                titlefilename = self._html_to_file(req, self._wikitext_to_html(req, titletext))
                filenames = [self._page_to_file(req, p) for p in pagenames]
        
                # Render
                htmldoc_args = { 'book': None, 'format': 'pdf14', 'titlefile': titlefilename, 'charset': codepage }
                htmldoc_args.update(dict(self.env.config.options('wikitopdf-admin')))
                if toctitle:
                        htmldoc_args['toctitle'] = '"' + toctitle.group(1) + '"'
        
                args_string = ' '.join(['--%s %s' % (arg, value or '') for arg, value
                                                in htmldoc_args.iteritems()])
        
                cmd_string = 'htmldoc %s %s -f %s'%(args_string, ' '.join(filenames), pfilename)
                self.log.info('WikitoPDF: Running %r', cmd_string)
                os.system(cmd_string.encode('latin-1'))
                   
                # Clean up
                os.unlink(titlefilename)
                for f in filenames:
                    os.unlink(f)

        else:
                html = self._wikitext_to_html(req, text)
                hfilename = self._html_to_file(req, html)
        
                pfile, pfilename = mkstemp('wikitopdf')
                os.close(pfile)
        
                htmldoc_args = { 'webpage': None, 'format': 'pdf14', 'charset': codepage }
                htmldoc_args.update(dict(self.env.config.options('wikitopdf-page')))
        
                args_string = ' '.join(['--%s %s' % (arg, value or '') for arg, value
                                        in htmldoc_args.iteritems()])
        
                self.env.log.debug('WikitoPDF => Htmldoc code out: %s' % args_string)
                os.system('htmldoc %s %s -f %s' % (args_string, hfilename, pfilename))
        
                os.unlink(hfilename)

        out = open(pfilename, 'rb').read()
        os.unlink(pfilename)
        return (out, 'application/pdf')


    # convert wiki text to clean html
    def _wikitext_to_html(self, req, wikitext):

        # htmldoc doesn't support utf-8, we need to use some other input encoding
        codepage = self.env.config.get('trac', 'charset', 'iso-8859-1')
        base_dir = self.env.config.get('wikitopdf', 'base_dir')

        # modify wiki text
        for r in EXCLUDE_RES:
                wikitext = r.sub('', wikitext)
            
        # convert wiki text to html...
        page = wiki_to_html(wikitext, self.env, req).encode(codepage, 'replace')

        # .. and clean up html
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
        return page
            

    # save html content (without html/body) to a complete html file
    def _html_to_file(self, req, html):

        # htmldoc doesn't support utf-8, we need to use some other input encoding
        codepage = self.env.config.get('trac', 'charset', 'iso-8859-1')

        hfile, hfilename = mkstemp('wikitopdf')
        meta = ('<meta http-equiv="Content-Type" content="text/html; charset=%s"/>' % codepage).encode(codepage)
        os.write(hfile, '<html><head>' + meta + '</head><body>' + html + '</body></html>')
        os.close(hfile)
        return hfilename
         
        
    def _page_to_file(self, req, pagename):

        wikitext = WikiPage(self.env, pagename).text
        html = self._wikitext_to_html(req, wikitext)
        return self._html_to_file(req, html)
