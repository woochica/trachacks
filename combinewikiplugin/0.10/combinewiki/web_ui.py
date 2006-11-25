
# TracCombineWiki plugin
# Copyright 2006 Noah Kantrowitz

from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.web.api import RequestDone
from trac.wiki.api import WikiSystem
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage
from trac.mimeview.api import Mimeview

from webadmin.web_ui import IAdminPageProvider

from tempfile import mkstemp
import os, re

class CombineWikiModule(Component):
    """A plugin allowing the export of multiple wiki pages in a single file."""

    implements(ITemplateProvider, IAdminPageProvider)
    
    EXCLUDE_RES = [
        re.compile('\[\[PageOutline([^]]*)\]\]'),
        re.compile('----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I)
    ]
    
    TITLE_HTML = u"""
    <table><tr><td height="100%%" width="100%%" align="center" valign="middle">
    <h1>%s</h1>
    </td></tr></table>
    """

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        #return [['combinewiki', resource_filename(__name__, 'htdocs'))]
        return []

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('WIKI_ADMIN'):
            yield ('general', 'General', 'combinewiki', 'Combine Wiki')

    def process_admin_request(self, req, cat, page, path_info):
        allpages = list(WikiSystem(self.env).get_pages())
        rightpages = [x for x in req.session.get('combinewiki_rightpages', '').split(',') if x]
        
        if req.method == 'POST':
            rightpages = req.args.get('rightpages_all')
            title = req.args.get('title') or self.env.project_name
            req.session['combinewiki_rightpages'] = rightpages
            rightpages = rightpages.split(',')
            
            # Dump all pages to HTML files
            files = [self._page_to_file(req, p) for p in rightpages]
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
            self.log.debug('CombineWikiModule: Running %r', cmd_string)
            os.system(cmd_string)
            
            #os.system('htmldoc --charset %s --book --format pdf14 --title --titlefile %s --header .t. --tocheader .t. --left 1.5cm --right 1.5cm --top 1.5cm --bottom 1.5cm %s -f %s' % (codepage.replace('iso-', ''), titlefile,' '.join(files), pfilename))     
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

            req.redirect(req.href.admin(cat, page))
        
        req.hdf['combinewiki.allpages'] = allpages
        leftpages = [x for x in allpages if x not in rightpages]
        leftpages.sort()
        req.hdf['combinewiki.leftpages'] = leftpages
        req.hdf['combinewiki.rightpages'] = rightpages

        return 'combinewiki_admin.cs', None

    def _page_to_file(self, req, pagename, text=None):
        """Slight modification of some code from Alec's PageToPdf plugin."""
        hfile, hfilename = mkstemp('tracpdf')
        codepage = Mimeview(self.env).default_charset

        self.log.debug('CombineWikiModule: Writting %s to %s using encoding %s', pagename, hfilename, codepage)

        page = text
        if text is None:
            text = WikiPage(self.env, pagename).text
            for r in self.EXCLUDE_RES:
                text = r.sub('', text)
            page = wiki_to_html(text, self.env, req).encode(codepage)
        self.log.debug('CombineWikiModule: Page text is %r', page)

        page = re.sub('<img src="(?!\w+://)', '<img src="%s://%s:%d' % (req.scheme, req.server_name, req.server_port), page)
        os.write(hfile, u'<html><head><title>' + pagename + u'</title></head><body>' + page + u'</body></html>')
        os.close(hfile)
        return hfilename
