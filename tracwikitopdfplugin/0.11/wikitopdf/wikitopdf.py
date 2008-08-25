"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

from trac.core import *
from trac.util import escape
from trac.mimeview.api import IContentConverter
from trac.wiki.formatter import wiki_to_html
from tempfile import mkstemp
import os
import re

EXCLUDE_RES = [
    re.compile(r'\[\[PageOutline([^]]*)\]\]'),
    re.compile(r'\[\[TracGuideToc([^]]*)\]\]'),
    re.compile(r'----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I)
]


def wiki_to_pdf(text, env, req, base_dir, codepage):
    
    env.log.debug('WikiToPdf => Start function wiki_to_pdf')

    #Remove exclude expressions
    for r in EXCLUDE_RES:
        text = r.sub('', text)
    
    env.log.debug('WikiToPdf => Wiki intput for WikiToPdf: %r' % text)
    
    page = wiki_to_html(text, env, req)
    page = page.replace('raw-attachment', 'attachments')
    page = page.replace('<img', '<img border="0"')
    page = page.replace('?format=raw', '')

    """I need improve this... Ticket #3427"""
    page = page.replace('<a class="wiki" href="/' + env.config.get('wikitopdf', 'folder_name') + '/wiki/', '<a class="wiki" href="' 
			+ env.config.get('wikitopdf', 'link') + '/wiki/')

    page = page.replace('<pre class="wiki">', '<table align="center" width="95%" border="1" bordercolor="#d7d7d7">'
                        + '<tr><td bgcolor="#f7f7f7"><pre class="wiki">')
    page = page.replace('</pre>', '</pre></td></tr></table>')
    page = page.replace('<table class="wiki">', '<table class="wiki" border="1" width="100%">')

    imgpos = page.find('<img')

    while imgpos != -1:
        addrpos = page.find('src=',imgpos)
	#base_dir = base_dir.encode('ascii')
        page = page[:addrpos+5] + base_dir + page[addrpos+5:]
        imgpos = page.find('<img', addrpos)
    
    meta = ('<meta http-equiv="Content-Type" content="text/html; charset=%s"/>' % codepage).encode(codepage)

    page = '<html><head>' + meta + '</head><body>' + page + '</body></html>'
    
    env.log.debug('WikiToPdf => HTML output for WikiToPdf in charset %s is: %r' % (codepage, page))    
    env.log.debug('WikiToPdf => Finish function wiki_to_pdf')

    return page.encode(codepage)

def html_to_pdf(env, htmldoc_args, files, codepage):

    env.log.debug('WikiToPdf => Start function html_to_pdf')

    os.environ["HTMLDOC_NOCGI"] = 'yes'
    
    args_string = ' '.join(['--%s %s' % (arg, value or '') for arg, value
        in htmldoc_args.iteritems() if value != None])
    
    pfile, pfilename = mkstemp('wikitopdf')
    os.close(pfile)
    
    cmd_string = 'htmldoc %s %s -f %s'%(args_string, ' '.join(files), pfilename)
    env.log.debug('WikiToPdf => Htmldoc command line: %s' % cmd_string)
    os.system(cmd_string.encode(codepage))
    
    infile = open(pfilename, 'rb') 
    out = infile.read()
    infile.close()
    
    os.unlink(pfilename)
    
    env.log.debug('WikiToPdf => Finish function html_to_pdf')

    return out

class WikiToPdfPage(Component):
    """Convert Wiki pages to PDF using HTMLDOC (http://www.htmldoc.org/)."""
    implements(IContentConverter)

        
    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('pdf', 'WikiToPdf', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)

    def convert_content(self, req, input_type, text, output_type):

        # htmldoc doesn't support utf-8, we need to use some other input encoding
        codepage = self.env.config.get('trac', 'charset', 'iso-8859-1')
        base_dir = self.env.config.get('wikitopdf', 'base_dir')

        page = wiki_to_pdf(text, self.env, req, base_dir, codepage)

        hfile, hfilename = mkstemp('wikitopdf')
        os.write(hfile, page)
        os.close(hfile)

        htmldoc_args = { 'webpage': '', 'format': 'pdf14', 'charset': codepage }
        htmldoc_args.update(dict(self.env.config.options('wikitopdf-page')))

        out = html_to_pdf(self.env, htmldoc_args, [hfilename], codepage)
        os.unlink(hfilename)

        return (out, 'application/pdf')
