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

class WikitoPDFPage(Component):
    """Convert Wiki pages to PDF using HTMLDOC (http://www.htmldoc.org/)."""
    implements(IContentConverter)

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('pdf', 'WikitoPDF', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)

    def convert_content(self, req, input_type, text, output_type):

	os.system("rm -f /tmp/tmp*wikitopdf")

	base_dir = self.env.config.get('wikitopdf', 'base_dir')

	hfile, hfilename = mkstemp('wikitopdf')
	# htmldoc doesn't support utf-8, we need to use some other input encoding

	codepage = self.env.config.get('trac', 'charset', 'iso-8859-1')

	for r in EXCLUDE_RES:
		text = r.sub('', text)
		
	page = wiki_to_html(text, self.env, req).encode(codepage, 'replace')

	self.env.log.debug('WikitoPDF => HTML output for WikiToPDF in charset: %s' % codepage)
        self.env.log.debug('WikitoPDF => HTML intput for WikiToPDF: %s' % text)

	page = page.replace('attachment', 'attachments')
	page = page.replace('?format=raw','')
        page = page.replace('<pre class="wiki">', '<table align="center" width="95%" border="1" bordercolor="#d7d7d7">'
	                                        + '<tr><td bgcolor="#f7f7f7"><pre class="wiki">')
        page = page.replace('</pre>', '</pre></td></tr></table>')
	page = page.replace('<table class="wiki">', '<table class="wiki" border="1" width="100%">')
	
	imgpos = page.find('<img')

	while imgpos != -1:
		addrpos = page.find('src=',imgpos)
		base_dir = base_dir.encode('ascii')
		page = page[:addrpos+5] + base_dir + page[addrpos+5:]
		imgpos = page.find('<img', addrpos)

	self.env.log.debug('WikitoPDF => Html code: %r' % page)

	meta = ('<meta http-equiv="Content-Type" content="text/html; charset=%s"/>' % codepage).encode(codepage)

        os.write(hfile, '<html><head>' + meta + '</head><body>' + page + '</body></html>')
        os.close(hfile)

        pfile, pfilename = mkstemp('wikitopdf')
        os.close(pfile)

	os.environ["HTMLDOC_NOCGI"] = 'yes'
        htmldoc_args = { 'webpage': None, 'format': 'pdf14', 'charset': codepage }

	htmldoc_args.update(dict(self.env.config.options('wikitopdf-page')))

        args_string = ' '.join(['--%s %s' % (arg, value or '') for arg, value
                                in htmldoc_args.iteritems()])

	self.env.log.debug('WikitoPDF => Htmldoc code out: %s' % args_string)

        os.system('htmldoc %s %s -f %s' % (args_string, hfilename, pfilename))

        out = open(pfilename, 'rb').read()
        os.unlink(pfilename)
        os.unlink(hfilename)
        return (out, 'application/pdf')
