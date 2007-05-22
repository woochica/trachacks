from trac import config
from trac.core import *
from trac.util import escape
from trac.mimeview.api import IContentConverter
from trac.util.html import Markup
from trac.wiki.api import WikiSystem
from StringIO import StringIO
import cElementTree as ElementTree
import os
import re
import zipfile
from odtformatter import wiki_to_odt

dump_contents = True

class PageToODTPlugin(Component):
    """Convert Wiki pages to ODT"""
    implements(IContentConverter)

    style_list = [ 'heading1', 'heading2', 'heading3', 'heading4']

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('odt', 'OpenDocument', 'odt', 'text/x-trac-wiki',
        'application/vnd.oasis.opendocument.text', 5)

    def convert_content(self, req, input_type, source, output_type):
        self.load_conf()
        archive = zipfile.ZipFile(self.template_filename, 'r')

	out = StringIO()
        out_arc = zipfile.ZipFile(out, 'w')

        for fileinfo in archive.infolist():
            if fileinfo.filename == 'content.xml':
                content = self.wiki_to_odtcontent(
                    req, source, archive.read(fileinfo.filename) )
                if dump_contents:
                    f = open('/tmp/lastcontent.xml', 'w')
                    f.write(content)
                    f.close()
            else:
                content = archive.read(fileinfo.filename)
            out_arc.writestr(fileinfo, content)

        out_arc.close()
        return out.getvalue(), 'application/vnd.oasis.opendocument.text'

    def load_conf(self):
        self.styles = {}
        self.template_filename = None

        wiki_system = WikiSystem(self.env)
        if not wiki_system.has_page('PageToOdtStyles'):
            raise Exception, 'Please create a PageToOdtStyles wiki page.'
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT text FROM wiki WHERE name = 'PageToOdtStyles' ORDER BY version DESC LIMIT 1")
        for (text,) in cursor:
            page_content = text
            break
        
        for line in page_content.strip().splitlines():
            if line.find('=') != -1:
                name, value = [token.strip()
                    for token in line.split("=", 2)]
                if name.startswith('style_'):
                    self.styles[ name[6:] ] = value
                elif name == 'template':
                    self.template_filename = os.path.join(
                        self.env.path, 'attachments', 'wiki',
                        'PageToOdtStyles', value)

    def wiki_to_odtcontent(self, req, source, template):
        officens = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
        textns = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'

        document_content = ElementTree.fromstring(template)

        text = document_content.find('{%s}body/{%s}text'
            % (officens, officens))

        if dump_contents:
            open('/tmp/raw.xml', 'w').write(
                wiki_to_odt(source, self.env, req, self.styles))
        new_content = ElementTree.fromstring(
            wiki_to_odt(source, self.env, req, self.styles))

        new_text = new_content.find('{%s}body/{%s}text'
            % (officens, officens))

        for node in new_text:
            text.append(node)

        return ElementTree.tostring(document_content)
            

#vim: tabstop=4 shiftwidth=4 expandtab
