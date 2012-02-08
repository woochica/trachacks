"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""
import os
import random
import re
import xml.sax.saxutils
from urllib import urlretrieve
from tempfile import NamedTemporaryFile, mkstemp
from trac.core import *
from trac.mimeview.api import Context, IContentConverter
from trac.util import escape
from trac.wiki.formatter import format_to_html

EXCLUDE_RES = [
    re.compile(r'\[\[PageOutline([^]]*)\]\]'),
    re.compile(r'\[\[TracGuideToc([^]]*)\]\]'),
    re.compile(r'\[\[TOC([^]]*)\]\]'),
    re.compile(r'----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I)
]

IMG_CACHE = { }

def tagattrfind(page, tag, attr, pos):
    tb_pos = page.find('<%s' % tag, pos)

    while tb_pos != -1:
        te_pos = page.find('>', tb_pos)
        tc_pos = page.find(attr, tb_pos, te_pos)

	if tc_pos != -1:
	    return tb_pos, te_pos+1

        tb_pos = page.find('<%s' % tag, te_pos+1)

    return -1, -1


def wiki_to_pdf(text, env, req, base_dir, codepage):
    global IMG_CACHE
    
    env.log.debug('WikiToPdf => Start function wiki_to_pdf')

    #Remove exclude expressions
    for r in EXCLUDE_RES:
        text = r.sub('', text)
    
    env.log.debug('WikiToPdf => Wiki intput for WikiToPdf: %r' % text)
        
    context = Context.from_request(req)
    page = format_to_html(env, context, text)
    
    page = page.replace('<img', '<img border="0"')
    page = page.replace('?format=raw', '')

    """I need improve this... Ticket #3427"""
    page = page.replace('<a class="wiki" href="/' + env.config.get('wikitopdf', 'folder_name') + '/wiki/', '<a class="wiki" href="' 
			+ env.config.get('wikitopdf', 'link') + '/wiki/')

    page = page.replace('<pre class="wiki">', '<table align="center" width="95%" border="1" bordercolor="#d7d7d7">'
                        + '<tr><td bgcolor="#f7f7f7"><pre class="wiki">')
    page = page.replace('</pre>', '</pre></td></tr></table>')
    page = page.replace('<table class="wiki">', '<table class="wiki" border="1" width="100%">')
    tracuri = env.config.get('wikitopdf', 'trac_uri')
    tmp_dir = env.config.get('wikitopdf', 'tmp_dir')
    
    if tracuri != '' and tmp_dir != '':
        # Download images so that dynamic images also work right
        # Create a random prefix
        random.seed()
        tmp_dir += '/%(#)04x_' %{"#":random.randint(0,65535)}
        # Create temp dir
        os.system('mkdir %s 2>/dev/null' % (tmp_dir))

        imgcounter = 0
        imgpos = page.find('<img')

        while imgpos != -1:
            addrpos = page.find('src="',imgpos)
            theimg = page[addrpos+5:]
            thepos = theimg.find('"')
            theimg = theimg[:thepos]
            if theimg[:1] == '/':
                theimg = tracuri + theimg
        try:
            newimg = IMG_CACHE[theimg]
        except:    
            #newimg = tmp_dir + '%(#)d_' %{"#":imgcounter} + theimg[theimg.rfind('/')+1:]
            file = NamedTemporaryFile(mode='w', prefix='%(#)d_' %{"#":imgcounter}, dir=tmp_dir)
            newimg = file.name
            file.close()
            #download
            theimg = xml.sax.saxutils.unescape(theimg)
            theimg = theimg.replace(" ","%20")
            urlretrieve(theimg, newimg)
            IMG_CACHE[theimg] = newimg
            env.log.debug("ISLAM the image is %s new image is %s" % ( theimg, newimg))
            imgcounter += 1

            page = page[:addrpos+5] + newimg + page[addrpos+5+thepos:]
            imgpos = page.find('<img', addrpos)

    else:
        # Use old search for images in path
        page = page.replace('raw-attachment', 'attachments')
        
        imgpos = page.find('<img')

        while imgpos != -1:
            addrpos = page.find('src=', imgpos)
#            base_dir = base_dir.encode('ascii')
            page = page[:addrpos+5] + base_dir + page[addrpos+5:]
            imgpos = page.find('<img', addrpos)
    
    # Add center tags, since htmldoc 1.9 does not handle align="center"
    (tablepos,tableend) = tagattrfind(page, 'table', 'align="center"', 0)
    while tablepos != -1:
        endpos = page.find('</table>',tablepos)
	page = page[:endpos+8] + '</center>' + page[endpos+8:]
        page = page[:tablepos] + '<center>' + page[tablepos:];

	endpos = page.find('</table>',tablepos)
        (tablepos,tableend) = tagattrfind(page, 'table', 'align="center"', endpos)

    # Add table around '<div class="code">'
    (tablepos,tableend) = tagattrfind(page, 'div', 'class="code"', 0)
    while tablepos != -1:
        endpos = page.find('</div>',tablepos)
        page = page[:endpos+6] + '</td></tr></table></center>' + page[endpos+6:]
        page = page[:tableend] + '<center><table align="center" width="95%" border="1" bordercolor="#d7d7d7"><tr><td>' + page[tableend:]

        endpos = page.find('</div>',tablepos)
        (tablepos,tableend) = tagattrfind(page, 'div', 'class="code"', endpos)

    # Add table around '<div class="system-message">'
    (tablepos,tableend) = tagattrfind(page, 'div', 'class="system-message"', 0)
    while tablepos != -1:
        endpos = page.find('</div>',tablepos)
        page = page[:endpos+6] + '</td></tr></table>' + page[endpos+6:]
        page = page[:tableend] + '<table width="100%" border="2" bordercolor="#dd0000" bgcolor="#ffddcc"><tr><td>' + page[tableend:]

        endpos = page.find('</div>',tablepos)
	(tablepos,tableend) = tagattrfind(page, 'div', 'class="system-message"', endpos)

    # Add table around '<div class="error">'
    (tablepos,tableend) = tagattrfind(page, 'div', 'class="error"', 0)
    while tablepos != -1:
        endpos = page.find('</div>',tablepos)
        page = page[:endpos+6] + '</td></tr></table>' + page[endpos+6:]
        page = page[:tableend] + '<table width="100%" border="2" bordercolor="#dd0000" bgcolor="#ffddcc"><tr><td>' + page[tableend:]

        endpos = page.find('</div>',tablepos)
        (tablepos,tableend) = tagattrfind(page, 'div', 'class="error"', endpos)

    # Add table around '<div class="important">'
    (tablepos,tableend) = tagattrfind(page, 'div', 'class="important"', 0)
    while tablepos != -1:
        endpos = page.find('</div>',tablepos)
        page = page[:endpos+6] + '</td></tr></table>' + page[endpos+6:]
        page = page[:tableend] + '<table width="100%" border="2" bordercolor="#550000" bgcolor="#ffccbb"><tr><td>' + page[tableend:]

        endpos = page.find('</div>',tablepos)
        (tablepos,tableend) = tagattrfind(page, 'div', 'class="important"', endpos)

    meta = ('<meta http-equiv="Content-Type" content="text/html; charset=%s"/>' % codepage)
    css = ''
    if env.config.get('wikitopdf', 'css_file') != '':
        css = ('<link rel="stylesheet" href="%s" type="text/css"/>' % env.config.get('wikitopdf', 'css_file')).encode(codepage)

    page = '<html><head>' + meta + css + '</head><body>' + page + '</body></html>'
    page = page.encode(codepage,'replace')
    
    env.log.debug('WikiToPdf => HTML output for WikiToPdf in charset %s is: %r' % (codepage, page))    
    env.log.debug('WikiToPdf => Finish function wiki_to_pdf')

    return page

def html_to_pdf(env, htmldoc_args, files, codepage):

    env.log.debug('WikiToPdf => Start function html_to_pdf')

    global IMG_CACHE
    os.environ["HTMLDOC_NOCGI"] = 'yes'
    
    args_string = ' '.join(['--%s %s' % (arg, value or '') for arg, value
        in htmldoc_args.iteritems() if value != None])
    
    pfile, pfilename = mkstemp('wikitopdf')
    os.close(pfile)
    
    cmd_string = 'htmldoc %s %s -f %s'%(args_string, ' '.join(files), pfilename)
    env.log.debug('WikiToPdf => Htmldoc command line: %s' % cmd_string)
    os.system(cmd_string.encode(codepage))

    # Delete files from tmp_dir
    for v in IMG_CACHE.values():
        if os.path.exists(v):
    	    os.unlink(v);
    IMG_CACHE = { }
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
        yield ('pdf', 'PDF', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)

    def convert_content(self, req, input_type, text, output_type):

        codepage = self.env.config.get('trac', 'default_charset', 'iso-8859-1') 
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
