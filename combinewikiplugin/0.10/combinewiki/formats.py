from trac.core import *
from trac.web.api import RequestDone
from trac.wiki.api import WikiSystem
from trac.wiki.formatter import wiki_to_html, Formatter, WikiProcessor
from trac.wiki.model import WikiPage
from trac.mimeview.api import Mimeview
from trac.util.text import shorten_line, to_unicode
from trac.util.html import Markup

from tempfile import mkstemp
from StringIO import StringIO
import os
import re
import time

from api import ICombineWikiFormat

EXCLUDE_RES = [
    re.compile(r'\[\[PageOutline([^]]*)\]\]'),
    re.compile(r'\[\[TracGuideToc([^]]*)\]\]'),
    re.compile(r'----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I)
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
        tiddlers = []
        #formatter = Formatter(self.env, req)
        formatter = TiddlyWikiFormatter(self.env, req)

        for name in pages:
            tiddler = {}
            tiddler['name'] = name
            page = WikiPage(self.env, name)
            tiddler['author'] = page.author
            tiddler['modtime'] = self._convert_time(page.time)
            page_1 = WikiPage(self.env, name, version=1)
            tiddler['ctime'] = self._convert_time(page_1.time)
                        
            out = StringIO()
            text = page.text
            for r in EXCLUDE_RES:
                    text = r.sub('', text)
            formatter.format(text, out)
            tiddler['content'] = out.getvalue()

            tiddlers.append(tiddler)


        def default_page(t, c):
            if t not in pages:
                tiddlers.append({
                    'name': t,
                    'modtime': self._convert_time(),
                    'ctime': self._convert_time(),
                    'content': c,
                })
        default_page('MainMenu', '\n'.join(pages))
        default_page('SiteTitle', title)
            
        req.hdf['combinewiki.tiddlers'] = tiddlers
        req.display('combinewiki_tiddlywiki.cs', 'text/html')
        
    def _convert_time(self, secs=None):
        if secs is not None:
            secs = int(secs)
        return time.strftime('%Y%m%d%H%M', time.localtime(secs))

class TiddlyWikiFormatter(Formatter):
    """Converter to go from Trac wiki to TiddlyWiki markup."""

    # Heading formatting    
    def _heading_formatter(self, match, fullmatch):
        self.close_table()
        self.close_paragraph()
        self.close_indentation()
        self.close_list()
        self.close_def_list()
        depth, heading, anchor = self._parse_heading(match, fullmatch, False)
        self.out.write('%s%s' %
                       (depth*'!', heading))
        
    def _parse_heading(self, match, fullmatch, shorten):
        match = match.strip()

        depth = min(len(fullmatch.group('hdepth')), 5)
        anchor = fullmatch.group('hanchor') or ''
        heading_text = match[depth+1:-depth-1-len(anchor)]
        out = StringIO()
        TiddlyWikiFormatter(self.env, self.req).format(heading_text, out)
        heading = Markup(out.getvalue().strip())
        if anchor:
            anchor = anchor[1:]
        else:
            sans_markup = heading.plaintext(keeplinebreaks=False)
            anchor = self._anchor_re.sub('', sans_markup)
            if not anchor or anchor[0].isdigit() or anchor[0] in '.-':
                # an ID must start with a Name-start character in XHTML
                anchor = 'a' + anchor # keeping 'a' for backward compat
        i = 1
        anchor_base = anchor
        while anchor in self._anchors:
            anchor = anchor_base + str(i)
            i += 1
        self._anchors[anchor] = True
        if shorten:
            heading = wiki_to_oneliner(heading_text, self.env, self.db, True,
                                       self._absurls)
        return (depth, heading, anchor)

    # Basic formatting
    def _bolditalic_formatter(self, match, fullmatch):
        return self.simple_tag_handler(match, "''//", "//''")

    def _bold_formatter(self, match, fullmatch):
        return self.simple_tag_handler(match, "''", "''")

    def _italic_formatter(self, match, fullmatch):
        return self.simple_tag_handler(match, '//', '//')

    def _underline_formatter(self, match, fullmatch):
        return self.simple_tag_handler(match, '__','__')

    def _strike_formatter(self, match, fullmatch):
        return self.simple_tag_handler(match, '--', '--')

    def _subscript_formatter(self, match, fullmatch):
        return self.simple_tag_handler(match, '~~', '~~')

    def _superscript_formatter(self, match, fullmatch):
        return self.simple_tag_handler(match, '^^', '^^')
        
    def _inlinecode_formatter(self, match, fullmatch):
        return '{{{' + fullmatch.group('inline') + '}}}'

    def _inlinecode2_formatter(self, match, fullmatch):
        return '{{{' + fullmatch.group('inline2') + '}}}'
        
    # Paragraph formatting
    def open_paragraph(self):
        if not self.paragraph_open:
            self.paragraph_open = 1
     
    def close_paragraph(self):
        if self.paragraph_open:
            while self._open_tags != []:
                self.out.write(self._open_tags.pop()[1])
            self.out.write(os.linesep)
            self.paragraph_open = 0

    def _list_formatter(self, match, fullmatch):
        ldepth = len(fullmatch.group('ldepth'))
        listid = match[ldepth]
        ldepth = ldepth//2 + 1
        self.in_list_item = True
        class_ = start = None
        if listid in '-*':
            type_ = 'ul'
            self.out.write('%s '%('*'*ldepth))
        else:
            self.out.write('%s '%('#'*ldepth))
            type_ = 'ol'
            idx = '01iI'.find(listid)
            if idx >= 0:
                class_ = ('arabiczero', None, 'lowerroman', 'upperroman')[idx]
            elif listid.isdigit():
                start = match[ldepth:match.find('.')]
            elif listid.islower():
                class_ = 'loweralpha'
            elif listid.isupper():
                class_ = 'upperalpha'
        #self._set_list_depth(ldepth, type_, class_, start)
        return ''
        
    def handle_code_block(self, line):
        if line.strip() == Formatter.STARTBLOCK:
            self.in_code_block += 1
            if self.in_code_block == 1:
                self.code_processor = None
                self.code_text = ''
            else:
                self.code_text += line + os.linesep
                if not self.code_processor:
                    self.code_processor = TiddlyWikiProcessor(self.env, 'default')
        elif line.strip() == Formatter.ENDBLOCK:
            self.in_code_block -= 1
            if self.in_code_block == 0 and self.code_processor:
                self.close_table()
                self.close_paragraph()
                self.out.write(to_unicode(self.code_processor.process(
                    self.req, self.code_text)))
            else:
                self.code_text += line + os.linesep
        elif not self.code_processor:
            match = Formatter._processor_re.search(line)
            if match:
                name = match.group(1)
                self.code_processor = TiddlyWikiProcessor(self.env, name)
            else:
                self.code_text += line + os.linesep 
                self.code_processor = TiddlyWikiProcessor(self.env, 'default')
        else:
            self.code_text += line + os.linesep

class TiddlyWikiProcessor(WikiProcessor):
    
    def _default_processor(self, req, text):
        return ''.join(['{{{\n', text, '}}}\n'])
