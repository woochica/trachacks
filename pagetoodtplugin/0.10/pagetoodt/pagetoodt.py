from trac import config
from trac.core import *
from trac.util import escape
from trac.mimeview.api import IContentConverter
from trac.wiki.formatter import wiki_to_html
from trac.util.html import Markup
from tempfile import mkstemp
import cElementTree as ElementTree
import os
import re
import zipfile

def wiki_to_odtcontent(source):
    officens = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
    textns = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'

    document_content = ElementTree.Element(
        '{%s}document-content' % officens)

    body = ElementTree.SubElement(document_content,
        '{%s}body' % officens)

    text = ElementTree.SubElement(body,
        '{%s}text' % officens)

    for line in source.splitlines():
	style = 'Standard'
        if line.startswith("= ") and line.endswith(" ="):
	    line = line[2:-2]
	    style = 'Titre 1'
        elif line.startswith("== ") and line.endswith(" =="):
	    line = line[3:-3]
	    style = 'Titre 2'
        elif line.startswith("=== ") and line.endswith(" ==="):
	    line = line[4:-4]
	    style = 'Titre 3'
        elif line.startswith("==== ") and line.endswith(" ===="):
	    line = line[5:-5]
	    style = 'Titre 5'
        elif line.startswith("[[") and line.endswith("]]"):
            continue

        p = ElementTree.SubElement(text,
            '{%s}p' % textns)
        p.set('{%s}style-name' % textns, style)
        p.text = line

    return ElementTree.tostring(document_content)

class PageToODTPlugin(Component):
    """Convert Wiki pages to ODT"""
    implements(IContentConverter)

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('odt', 'OpenDocument', 'odt', 'text/x-trac-wiki',
        'application/vnd.oasis.opendocument.text', 5)

    def convert_content(self, req, input_type, source, output_type):
        empty_path = self.env.config.get('pagetoodt', 'empty_template',
            os.path.join( config.default_dir('templates'), 'empty.odt'))
        archive = zipfile.ZipFile(empty_path, 'r')

        tfile, tfilename = mkstemp('tracodt')
        os.close(tfile)
        out_arc = zipfile.ZipFile(tfilename, 'w')

        for fileinfo in archive.infolist():
            if fileinfo.filename == 'content.xml':
                content = wiki_to_odtcontent( source )
		f = open('/tmp/lastcontent.xml', 'w')
		f.write(content)
		f.close()
            else:
                content = archive.read(fileinfo.filename)
            out_arc.writestr(fileinfo, content)

        out_arc.close()
        out = open(tfilename, 'rb').read()
        os.unlink(tfilename)
        return out, 'application/vnd.oasis.opendocument.text'

#vim: tabstop=4 shiftwidth=4 expandtab
