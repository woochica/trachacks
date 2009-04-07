"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
Modified by: Alvaro Iradier <alvaro.iradier@polartech.es>
"""

from trac.core import *
from trac.util import escape, Markup
from trac.mimeview.api import IContentConverter, Context
from trac.wiki.formatter import format_to_html
from trac.util.datefmt import format_datetime, to_datetime
from trac.util.text import to_unicode
from trac.wiki.model import WikiPage
from trac.resource import Resource
from pkg_resources import resource_filename
from trac.web.href import Href
import os
import re

import urllib2
import urlparse
import tempfile

import cStringIO
import ho.pisa as pisa
import defaults

# Kludge to workaround the lack of absolute imports in Python version prior to
# 2.5
pygments = __import__('pygments', {}, {}, ['lexers', 'styles', 'formatters'])
HtmlFormatter = pygments.formatters.html.HtmlFormatter
get_style_by_name = pygments.styles.get_style_by_name


EXCLUDE_RES = [
    re.compile(r'\[\[TracGuideToc([^]]*)\]\]'),
    re.compile(r'----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I),
]


def wikipage_to_html(text, page_name, env, req, replace_refs = True):
    """
    Converts a wiki text to HTML, and makes some replacements in order to fix
    internal and external links and references
    """

    env.log.debug('WikiPrint => Start function wikipage_to_html')

    #Remove exclude expressions
    for r in EXCLUDE_RES:
        text = r.sub('', text)
    
    #Escape [[PageOutline]], to avoid wiki processing
    text = text.replace('[[PageOutline]]', '![[PageOutline]]')

    env.log.debug('WikiPrint => Wiki input for WikiPrint: %r' % text)
    #Use format_to_html instead of old wiki_to_html
    
    #First create a Context object from the wiki page
    context = Context(Resource('wiki', page_name), req.abs_href, req.perm)
    context.req = req
    
    #Now convert in that context
    page = format_to_html(env, context, text)
    env.log.debug('WikiPrint => Wiki to HTML output: %r' % page)
    
    #If replace_refs, make relative URLS absolute, and change 'src' references to file references,
    #otherwise images and links won't work correctly
    if replace_refs:
        ###############################################
        #TODO: Improve this, maybe use regexs like:
        #<img src="http://absolute_url/path/to/env/raw-attachment/wiki/PageName/file.ext" 
        # ->
        #<img src="C:\path\to\env\attachments\wiki\PageName\file.ext" 
        #
        #<img src="http://http://absolute_url/path/to/env/raw-attachment/ticket/NUM/file.ext"
        # ->
        #<img src="C:\path\to\env\\attachments\ticket\NUM\file.ext
        ###############################################
        #The current solution will work for tickets and wiki images. What about htdocs: and source: ?
        page = page.replace('raw-attachment', 'attachments')
        page = page.replace('src="' + req.abs_href(), 'src="' + env.path)
    
    env.log.debug('WikiPrint => HTML output for WikiPrint is: %r' % page)
    env.log.debug('WikiPrint => Finish function wikipage_to_html')

    return page


def add_headers(env, page, codepage, book=False, title='', subject='', version='', date='', extra_headers = ''):
    """
    Add HTML standard begin and end tags, and header tags and styles.
    Add front page and extra contents (header/footer), replacing #EXPRESSIONS (title, subject, version and date)
    """

    extra_content = get_extracontent(env)
    extra_content = extra_content.replace('#TITLE', title)
    extra_content = extra_content.replace('#VERSION', version)
    extra_content = extra_content.replace('#DATE', date)
    extra_content = extra_content.replace('#SUBJECT', subject)
    

    if book:
        frontpage = get_frontpage(env)
        frontpage = frontpage.replace('#TITLE', title)
        frontpage = frontpage.replace('#VERSION', version)
        frontpage = frontpage.replace('#DATE', date)
        frontpage = frontpage.replace('#SUBJECT', subject)
        page = Markup(frontpage) + Markup(page)
        style = Markup(get_book_css(env))
    else:
        style = Markup(get_article_css(env))
    
    #Get pygment style
    try:
        style_cls = get_style_by_name('trac')
        parts = style_cls.__module__.split('.')
        filename = resource_filename('.'.join(parts[:-1]), parts[-1] + '.py')
        formatter = HtmlFormatter(style=style_cls)
        content = u'\n\n'.join([
            formatter.get_style_defs('div.code pre'),
            formatter.get_style_defs('table.code td')
        ]).encode('utf-8')
        style = style + Markup(content)
    except ValueError, e:
        pass
    
    
    page = Markup('<html><head>') + \
        Markup('<meta http-equiv="Content-Type" content="text/html; charset=%s"/>' % codepage) + \
        Markup(extra_headers) + \
        Markup('<style type="text/css">') + style + Markup('</style>') + \
        Markup('</head><body>%s' % extra_content) + \
        Markup(page) + \
        Markup('</body></html>')
        
    return page
    

def get_file_or_default(env, config_key, default):
    file = env.config.get('wikiprint', config_key)
    loader = linkLoader(env)
    if file: 
        file = loader.getFileName(file)
        env.log.debug("wikiprint => Loading URL: %s" % file)
        try:
            f = open(file)
            data = f.read()
            f.close()
        except:
            data = default
    else:
        data = default
    
    return to_unicode(data)

def get_css(env):
    return get_file_or_default(env, 'css_url', defaults.CSS)

def get_book_css(env):
    return get_file_or_default(env, 'book_css_url', defaults.BOOK_EXTRA_CSS)

def get_article_css(env):
    return get_file_or_default(env, 'article_css_url', defaults.ARTICLE_EXTRA_CSS)

def get_frontpage(env):
    return get_file_or_default(env, 'frontpage_url', defaults.FRONTPAGE)

def get_extracontent(env):
    return get_file_or_default(env, 'extracontent_url', defaults.EXTRA_CONTENT)

def get_toc(title):
    return Markup('<h1 style="-pdf-outline: false;">%s</h1><div><pdf:toc /></div><div><pdf:nextpage /></div>' % title)


class linkLoader:

    """
    Helper to load page from an URL and load corresponding
    files to temporary files. If getFileName is called it 
    returns the temporary filename and takes care to delete
    it when linkLoader is unloaded. 
    """
    
    def __init__(self, env):
        self.tfileList = []
        self.env = env
        self.env.log.debug('WikiPrint.linkLoader => Initializing')
    
    def __del__(self):
        for path in self.tfileList:
            self.env.log.debug("WikiPrint.linkLoader => deleting %s", path)
            os.remove(path)
            
    def getFileName(self, name, relative=''):
        try:
            if name.startswith('http://') or name.startswith('https://'):
                self.env.log.debug('WikiPrint.linkLoader => Resolving URL: %s' % name)
                url = urlparse.urljoin(relative, name)
                self.env.log.debug('WikiPrint.linkLoader => urljoined URL: %s' % url)
                path = urlparse.urlsplit(url)[2]
                self.env.log.debug('WikiPrint.linkLoader => path: %s' % path)
                suffix = ""
                if "." in path:
                    new_suffix = "." + path.split(".")[-1].lower()
                    if new_suffix in (".css", ".gif", ".jpg", ".png"):
                        suffix = new_suffix
                path = tempfile.mktemp(prefix="pisa-", suffix = suffix)            
                ufile = urllib2.urlopen(url)                     
                tfile = file(path, "wb")
                while True:
                    data = ufile.read(1024)
                    if not data:
                        break
                    # print data
                    tfile.write(data)
                ufile.close()
                tfile.close()
                self.tfileList.append(path)
                self.env.log.debug("WikiPrint.linkLoader => loading %s to %s", url, path)
                return path
            else:
                self.env.log.debug('WikiPrint.linkLoader => Resolving local path: %s' % name)
                return name
        except Exception, e:
            self.env.log.debug("WikiPrint.linkLoader ERROR: %s" % e)
        return None


def html_to_pdf(env, html_pages, codepage, book=True, title='', subject='', version='', date=''):
    
    env.log.debug('WikiPrint => Start function html_to_pdf')

    page = Markup('\n<div><pdf:nextpage /></div>'.join(html_pages))
    
    #Replace PageOutline macro with Table of Contents
    #TODO: Should not replace "![[PageOutline]]", only "[[PageOutline]]" !!!
    if book:
        #If book, remove [[PageOutlines]], and add at beginning
        page = page.replace('[[PageOutline]]','')
        page = Markup(get_toc(env.config.get('wikiprint', 'toc_title', 'Table of contents'))) + Markup(page)
    else:
        page = page.replace('[[PageOutline]]',get_toc(env.config.get('wikiprint', 'toc_title', 'Table of contents')))

    page = add_headers(env, page, codepage, book, title=title, subject=subject, version=version, date=date)
    page = page.encode(codepage, 'replace')
    css_data = get_css(env)

    pdf_file = cStringIO.StringIO()
    loader = linkLoader(env)
    pdf = pisa.CreatePDF(page, pdf_file, show_errors_as_pdf = True, default_css = css_data, link_callback = loader.getFileName)
    out = pdf_file.getvalue()
    pdf_file.close()

    env.log.debug('WikiPrint => Finish function html_to_pdf')

    return out


def html_to_printhtml(env, html_pages, codepage, title='', subject='', version='', date='', ):
    
    env.log.debug('WikiPrint => Start function html_to_printhtml')

    page = Markup('<hr>'.join(html_pages))
    
    css_data = '<style type="text/css">%s</style>' % get_css(env)
    page = add_headers(env, page, codepage, book=False, title=title, subject=subject, version=version, date=date, extra_headers = css_data)

    page = page.encode(codepage, 'replace')
    
    
    return page


class WikiToPDFPage(Component):
    """Convert Wiki pages to PDF using PISA"""
    implements(IContentConverter)
        
    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('pdfarticle', 'PDF Article', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)
        yield ('pdfbook', 'PDF Book', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)

    def convert_content(self, req, input_type, text, output_type):
        codepage = self.env.config.get('trac', 'default_charset', 'utf-8') 
        wikipage = WikiPage(self.env, req.args.get('page', 'WikiStart'))
        page = wikipage_to_html(text, req.args.get('page', 'WikiStart'), self.env, req, replace_refs = True)
        out = html_to_pdf(self.env, [page], codepage, book = (output_type == 'pdfbook'),
            title=wikipage.name,
            version=str(wikipage.version),
            date=format_datetime(to_datetime(None)))
        return (out, 'application/pdf')


class WikiToHtmlPage(Component):
    """Convert Wiki pages to HTML"""
    implements(IContentConverter)
        
    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('printhtml', 'Printable HTML', 'html', 'text/x-trac-wiki', 'text/html', 7)

    def convert_content(self, req, input_type, text, output_type):
        codepage = self.env.config.get('trac', 'default_charset', 'utf-8') 
        page = wikipage_to_html(text, req.args.get('page', 'WikiStart'), self.env, req, replace_refs = False)
        out = html_to_printhtml(self.env, [page], codepage)
        return (out, 'text/html')
