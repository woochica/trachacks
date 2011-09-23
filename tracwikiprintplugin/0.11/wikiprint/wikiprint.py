"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
Modified by: Alvaro Iradier <alvaro.iradier@polartech.es>
"""

from trac.core import *
from trac.util import escape, Markup
from trac.mimeview.api import IContentConverter, Context
from trac.wiki.formatter import format_to_html, OutlineFormatter
from trac.util import hex_entropy
from trac.util.datefmt import format_datetime, to_datetime
from trac.util.text import to_unicode
from trac.wiki.model import WikiPage
from trac.resource import Resource
from pkg_resources import resource_filename
from trac.web.href import Href
from trac.web.api import IAuthenticator
from trac.config import Option, BoolOption
import os
import re

import urllib2
import cookielib
import urlparse
import tempfile
import time

import StringIO
import ho.pisa as pisa
import defaults

# Kludge to workaround the lack of absolute imports in Python version prior to
# 2.5
pigments_loaded = False
try:
    #TODO: A better way of importing and checking pigments? Copied from trac.mimeview.pigments
    pygments = __import__('pygments', {}, {}, ['lexers', 'styles', 'formatters'])
    HtmlFormatter = pygments.formatters.html.HtmlFormatter
    get_style_by_name = pygments.styles.get_style_by_name
    pigments_loaded = True
except:
    pass


EXCLUDE_RES = [
    re.compile(r'\[\[TracGuideToc([^]]*)\]\]'),
    re.compile(r'----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I),
]

class linkLoader:

    """
    Helper to load page from an URL and load corresponding
    files to temporary files. If getFileName is called it 
    returns the temporary filename and takes care to delete
    it when linkLoader is unloaded. 
    """
    
    def __init__(self, env, req, auth_cookie = None, allow_local = False):
        self.tfileList = []
        self.env = env
        self.auth_cookie = auth_cookie
        self.req = req
        self.allow_local = allow_local
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
            elif self.allow_local:
                self.req.perm.assert_permission('WIKIPRINT_FILESYSTEM')
                self.env.log.debug("WikiPrint.linkLoader => Resolve local filesystem %s", name)
                return name
            else:
                #Relative path
                self.env.log.debug("WikiPrint.linkLoader => Relative path %s to %s", name, urlparse.urljoin(self.req.abs_href(), name))
                url = urlparse.urljoin(self.req.abs_href(), name)
                
            path = urlparse.urlsplit(url)[2]
            self.env.log.debug('WikiPrint.linkLoader => path: %s' % path)
            suffix = ""
            if "." in path:
                new_suffix = "." + path.split(".")[-1].lower()
                if new_suffix in (".css", ".gif", ".jpg", ".png"):
                    suffix = new_suffix
            path = tempfile.mktemp(prefix="pisa-", suffix = suffix)          
            
            #Allow wikiprint to authenticate using user and password, Basic HTTP Auth or Digest
            if self.env.config.get('wikiprint', 'httpauth_user'):
                pwmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
                pwmgr.add_password(None, url,
                    self.env.config.get('wikiprint', 'httpauth_user'),
                    self.env.config.get('wikiprint', 'httpauth_password'))
                auth_handler = urllib2.HTTPBasicAuthHandler(pwmgr)
                auth_handler2 = urllib2.HTTPDigestAuthHandler(pwmgr)
            
                opener = urllib2.build_opener(auth_handler, auth_handler2)
                urllib2.install_opener(opener)
            
            #Prepare the request with the auth cookie
            request = urllib2.Request(url)
            self.env.log.debug("Adding cookie to HTTP request: pdfgenerator_cookie=%s", self.auth_cookie)
            request.add_header("Cookie", "pdfgenerator_cookie=%s" % self.auth_cookie)
            
            #Make the request and download the file
            ufile = urllib2.urlopen(request)
            tfile = file(path, "wb")
            size = 0
            while True:
                data = ufile.read(1024)
                if not data:
                    break
                # print data
                size = size + len(data)
                tfile.write(data)
            ufile.close()
            tfile.close()
            self.tfileList.append(path)
            self.env.log.debug("WikiPrint.linkLoader => loading %s to %s, %d bytes", url, path, size)
            return path

        except Exception, e:
            self.env.log.debug("WikiPrint.linkLoader ERROR: %s" % e)
        return None


class WikiPrint(Component):
    """The core module where all conversion takes place. Enable it or the other modules won't work correctly"""    
    toc_title = Option('wikiprint', 'toc_title', 'Table of Contents')
    css_url = Option('wikiprint', 'css_url')
    book_css_url = Option('wikiprint', 'book_css_url')
    article_css_url = Option('wikiprint', 'article_css_url')
    frontpage_url = Option('wikiprint', 'frontpage_url')
    extracontent_url = Option('wikiprint', 'extracontent_url')
    httpauth_user = Option('wikiprint', 'httpauth_user')
    httpauth_password = Option('wikiprint', 'httpauth_password')
    omit_links = BoolOption('wikiprint', 'omit_links')
    rebase_links = Option('wikiprint', 'rebase_links')
    default_charset = Option('trac', 'default_charset', 'utf-8')
    
    implements(IAuthenticator)
    
    def _get_name_for_cookie(self, cookie):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM auth_cookie WHERE cookie=%s", (cookie.value,))
        row = cursor.fetchone()
        if not row:
            return None
        self.env.log.debug("Cookie for user: %s", row[0]);
        return row[0]

    # IAuthenticator methods
    def authenticate(self, req):
        authname = None
        self.env.log.debug("Trying pdfgenerator_cookie authentication")
        if req.incookie.has_key('pdfgenerator_cookie'):
            self.env.log.debug("Cookie found: %s", req.incookie['pdfgenerator_cookie'].value)
            authname = self._get_name_for_cookie(req.incookie['pdfgenerator_cookie'])
        
        return authname

    
    def wikipage_to_html(self, text, page_name, req):
        """
        Converts a wiki text to HTML, and makes some replacements in order to fix
        internal and external links and references
        """

        self.env.log.debug('WikiPrint => Start function wikipage_to_html')

        #Remove exclude expressions
        for r in EXCLUDE_RES:
            text = r.sub('', text)
        
        #Escape [[PageOutline]], to avoid wiki processing
        for r in [re.compile(r'\[\[TOC(\(.*\))?\]\]'), re.compile(r'\[\[PageOutline(\(.*\))?\]\]')]:
            text = r.sub('![[pdf-toc]]', text)

        link_format = req.args.get('link_format', None)
            
        if self.omit_links:
            r1 = re.compile(r'\[wiki:(.*?) (.*?)\]')
            text = r1.sub('[\g<2>]', text)            
            r2 = re.compile(r'\[wiki:(.*?)\]')
            text = r2.sub('[\g<1>]', text)            
        elif link_format:
            #Keep links to the same export format
            r = re.compile(r'(?<=\[wiki:)(.*?)(?=(?: .*?)?\])')
            text = r.sub('\g<1>?format=%s&link_format=%s' % (link_format, link_format), text)
            
        if self.rebase_links:
            r = re.compile(r'\[wiki:(.*?)\]')
            text = r.sub('[%s/wiki/\g<1>]' % self.rebase_links, text)

        self.env.log.debug('WikiPrint => Wiki input for WikiPrint: %r' % text)
        
        #First create a Context object from the wiki page
        context = Context(Resource('wiki', page_name), req.abs_href, req.perm)
        context.req = req
        
        #Now convert in that context
        page = format_to_html(self.env, context, text)
        self.env.log.debug('WikiPrint => Wiki to HTML output: %r' % page)
        
        self.env.log.debug('WikiPrint => HTML output for WikiPrint is: %r' % page)
        self.env.log.debug('WikiPrint => Finish function wikipage_to_html')

        return page


    def html_to_pdf(self, req, html_pages, book=True, title='', subject='', version='', date=''):
        
        self.env.log.debug('WikiPrint => Start function html_to_pdf')

        page = Markup('\n<div><pdf:nextpage /></div>'.join(html_pages))
        
        #Replace PageOutline macro with Table of Contents
        if book:
            #If book, remove [[TOC]], and add at beginning
            page = page.replace('[[pdf-toc]]','')
            page = Markup(self.get_toc()) + Markup(page)
        else:
            page = page.replace('[[pdf-toc]]',self.get_toc())

        page = self.add_headers(req, page, book, title=title, subject=subject, version=version, date=date)
        page = page.encode(self.default_charset, 'replace')
        css_data = self.get_css(req)

        pdf_file = StringIO.StringIO()

        auth_cookie = hex_entropy()
        loader = linkLoader(self.env, req, auth_cookie)

        #Temporary authentication
        self.env.log.debug("Storing temporary auth cookie %s for user %s", auth_cookie, req.authname)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("INSERT INTO auth_cookie (cookie,name,ipnr,time) "
            "VALUES (%s, %s, %s, %s)", (auth_cookie, req.authname, '127.0.0.1', int(time.time())))
        db.commit()        
        
        pdf = pisa.CreatePDF(page, pdf_file, show_errors_as_pdf = True, default_css = css_data, link_callback = loader.getFileName)
        out = pdf_file.getvalue()
        pdf_file.close()
        
        cursor.execute("DELETE FROM auth_cookie WHERE cookie=%s", (auth_cookie,))
        db.commit()        

        self.env.log.debug('WikiPrint => Finish function html_to_pdf')

        return out

    def html_to_printhtml(self, req, html_pages, title='', subject='', version='', date='', ):
        
        self.env.log.debug('WikiPrint => Start function html_to_printhtml')

        page = Markup('<hr>'.join(html_pages))
        
        #TO-DO: Make a nice TOC for HTML printable output
        page = page.replace('[[pdf-toc]]','')        
        
        css_data = '<style type="text/css">%s</style>' % self.get_css(req)
        page = self.add_headers(req, page, book=False, title=title, subject=subject, version=version, date=date, extra_headers = css_data)

        page = page.encode(self.default_charset, 'replace')
        
        return page
        
    def add_headers(self, req, page, book=False, title='', subject='', version='', date='', extra_headers = ''):
        """
        Add HTML standard begin and end tags, and header tags and styles.
        Add front page and extra contents (header/footer), replacing #EXPRESSIONS (title, subject, version and date)
        """

        extra_content = self.get_extracontent(req)
        extra_content = extra_content.replace('#TITLE', title)
        extra_content = extra_content.replace('#VERSION', version)
        extra_content = extra_content.replace('#DATE', date)
        extra_content = extra_content.replace('#SUBJECT', subject)
        

        if book:
            frontpage = self.get_frontpage(req)
            frontpage = frontpage.replace('#TITLE', title)
            frontpage = frontpage.replace('#VERSION', version)
            frontpage = frontpage.replace('#DATE', date)
            frontpage = frontpage.replace('#SUBJECT', subject)
            page = Markup(frontpage) + Markup(page)
            style = Markup(self.get_book_css(req))
        else:
            style = Markup(self.get_article_css(req))
        
        #Get pygment style
        if pigments_loaded:
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
            Markup('<meta http-equiv="Content-Type" content="text/html; charset=%s"/>' % self.default_charset) + \
            Markup(extra_headers) + \
            Markup('<style type="text/css">') + style + Markup('</style>') + \
            Markup('</head><body>%s' % extra_content) + \
            Markup(page) + \
            Markup('</body></html>')
            
        return page
        
    def get_file_or_default(self, req, file_or_url, default):
        loader = linkLoader(self.env, req, allow_local=True)
        if file_or_url: 
            file_or_url = loader.getFileName(file_or_url)
            self.env.log.debug("wikiprint => Loading URL: %s" % file_or_url)
            try:
                f = open(file_or_url)
                data = f.read()
                f.close()
            except:
                data = default
        else:
            data = default
        
        return to_unicode(data)

    def get_css(self, req):
        return self.get_file_or_default(req, self.css_url, defaults.CSS)

    def get_book_css(self, req):
        return self.get_file_or_default(req, self.book_css_url, defaults.BOOK_EXTRA_CSS)

    def get_article_css(self, req):
        return self.get_file_or_default(req, self.article_css_url, defaults.ARTICLE_EXTRA_CSS)

    def get_frontpage(self, req):
        return self.get_file_or_default(req, self.frontpage_url, defaults.FRONTPAGE)

    def get_extracontent(self, req):
        return self.get_file_or_default(req, self.extracontent_url, defaults.EXTRA_CONTENT)

    def get_toc(self):
        return Markup('<h1 style="-pdf-outline: false;">%s</h1><div><pdf:toc /></div><div><pdf:nextpage /></div>' % self.toc_title)


class WikiToPDFPage(Component):    
    """Add an option in wiki pages to export to PDF using PISA"""
    
    implements(IContentConverter)
    
    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('pdfarticle', 'PDF Article', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)
        yield ('pdfbook', 'PDF Book', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)

    def convert_content(self, req, input_type, text, output_type):
        page_name = req.args.get('page', 'WikiStart')
        wikipage = WikiPage(self.env, page_name)
        
        wikiprint = WikiPrint(self.env)
        
        page = wikiprint.wikipage_to_html(text, page_name, req)
        
        #Get page title from first header in outline
        out = StringIO.StringIO()
        context = Context(Resource('wiki', page_name), req.abs_href, req.perm)
        context.req = req

        outline = OutlineFormatter(self.env, context)
        outline.format(text, out, 1, 1)
        
        title = wikipage.name
        for depth, anchor, text in outline.outline:
            if depth == 1:
                title = text
                break
        
        out = wikiprint.html_to_pdf(req, [page], book = (output_type == 'pdfbook'),
            title=title,
            subject="%s - %s" % (self.env.project_name, page_name),
            version=str(wikipage.version),
            date=format_datetime(to_datetime(None)))
        return (out, 'application/pdf')


class WikiToHtmlPage(WikiPrint):
    """Add an option in wiki pages to export to printable HTML"""
    implements(IContentConverter)
        
    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('printhtml', 'Printable HTML', 'html', 'text/x-trac-wiki', 'text/html', 7)

    def convert_content(self, req, input_type, text, output_type):
        
        wikiprint = WikiPrint(self.env)
        
        page = wikiprint.wikipage_to_html(text, req.args.get('page', 'WikiStart'), req)
        out = wikiprint.html_to_printhtml(req, [page], self.default_charset)
        return (out, 'text/html')
