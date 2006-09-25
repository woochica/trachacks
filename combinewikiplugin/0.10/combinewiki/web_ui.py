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
        re.compile('\[\[PageOutline\]\]'),
        re.compile('----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I)
    ]

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
            req.session['combinewiki_rightpages'] = rightpages
            rightpages = rightpages.split(',')
            
            # Dump all pages to HTML files
            files = {}
            for p in rightpages:
                files[p] = self._page_to_file(req, p)
            
            # File to write PDF to
            pfile, pfilename = mkstemp('tracpdf')
            os.close(pfile)       
            
            # Render
            os.environ["HTMLDOC_NOCGI"] = 'yes'
            codepage = Mimeview(self.env).default_charset
            os.system('htmldoc --charset %s --book --format pdf14 --left 1.5cm --right 1.5cm --top 1.5cm --bottom 1.5cm %s -f %s' % (codepage.replace('iso-', ''), ' '.join([files[p] for p in rightpages]), pfilename))     
            out = open(pfilename, 'rb').read()
            
            # Clean up
            os.unlink(pfilename)
            for f in files.itervalues():
                os.unlink(f)
              
            # Send the output
            req.send_response(200)
            req.send_header('Content-Type', 'application/pdf')
            req.send_header('Content-Length', len(out))
            req.end_headers()
            req.write(out)
            raise RequestDone

            req.redirect(req.href.admin(cat, page))
        
        req.hdf['combinewiki.allpages'] = allpages
        req.hdf['combinewiki.leftpages'] = [x for x in allpages if x not in rightpages]
        req.hdf['combinewiki.rightpages'] = rightpages

        return 'combinewiki_admin.cs', None

    def _page_to_file(self, req, pagename):
        """Slight modification of some code from Alec's PageToPdf plugin."""
        hfile, hfilename = mkstemp('tracpdf')
        codepage = Mimeview(self.env).default_charset

        self.log.debug('CombineWikiModule: Writting %s to %s', pagename, hfilename)

        text = WikiPage(self.env, pagename).text
        for r in self.EXCLUDE_RES:
            text = r.sub('', text)

        page = wiki_to_html(text, self.env, req).encode(codepage)
        page = page.replace(r'<img src="', '<img src="%s://%s/' % (req.scheme, req.server_name))
        os.write(hfile, u'<html><head><title>' + pagename + u'</title></head><body>' + page + u'</body></html>')
        os.close(hfile)
        return hfilename
