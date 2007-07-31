from trac.core import *
from trac.util import escape
from trac.mimeview.api import IContentConverter
from trac.wiki.formatter import wiki_to_html
import os
import re
from cStringIO import StringIO
from tidy import parseString
import libxml2
import libxslt
from pkg_resources import resource_filename


class PageToDocbookPlugin(Component):
    """Convert Wiki pages to docbook."""
    implements(IContentConverter)

    def wiki_to_docbook(wikitext, env, req, db=None, absurls=False, escape_newlines=False):
        if not wikitext:
            return ""
        out = StringIO()
        DocbookFormatter(env, req, absurls, db).format(wikitext, out, escape_newlines)
        return out.getvalue()


    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('docbook', 'Docbook', 'docbook', 'text/x-trac-wiki', 'application/docbook+xml', 7)

    def convert_content(self, req, input_type, source, output_type):
        html = wiki_to_html(source, self.env, req)
	options = dict(output_xhtml=1, add_xml_decl=1, indent=1, tidy_mark=0, input_encoding='utf8', output_encoding='utf8', doctype='omit', wrap=0, char_encoding='utf8')
	xhtml = parseString(html.encode("utf-8"), **options)

	xhtml2dbXsl = u"""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href=\"""" + resource_filename(__name__, 'data/html2db/html2db.xsl') + """\" />
  <xsl:output method="xml" indent="no" encoding="utf-8"/>
  <xsl:param name="document-root" select="'chapter'"/>
</xsl:stylesheet>
"""

	normalizedHeadingsXsl = u"""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href=\"""" + resource_filename(__name__, 'data/headingsNormalizer/headingsNormalizer.xsl') + """\" />
  <xsl:output method="xml" indent="no" encoding="utf-8"/>
  <xsl:param name="defaultTopHeading" select="'""" + req.path_info[6:] + """'"/>
</xsl:stylesheet>
"""

	xhtml_xmldoc = libxml2.parseDoc(str(xhtml))

	normalizedHeadingsXsl_xmldoc = libxml2.parseDoc(normalizedHeadingsXsl)
	normalizedHeadingsXsl_xsldoc = libxslt.parseStylesheetDoc(normalizedHeadingsXsl_xmldoc)
	xhtml2_xmldoc = normalizedHeadingsXsl_xsldoc.applyStylesheet(xhtml_xmldoc, None)

	nhstring = normalizedHeadingsXsl_xsldoc.saveResultToString(xhtml2_xmldoc)

	xhtml2dbXsl_xmldoc = libxml2.parseDoc(xhtml2dbXsl)
	xhtml2dbXsl_xsldoc = libxslt.parseStylesheetDoc(xhtml2dbXsl_xmldoc)
	docbook_xmldoc = xhtml2dbXsl_xsldoc.applyStylesheet(xhtml2_xmldoc, None)

	dbstring = xhtml2dbXsl_xsldoc.saveResultToString(docbook_xmldoc)

	xhtml_xmldoc.freeDoc()
	normalizedHeadingsXsl_xsldoc.freeStylesheet()
	xhtml2dbXsl_xsldoc.freeStylesheet()
	xhtml2_xmldoc.freeDoc()
	docbook_xmldoc.freeDoc()
	return (dbstring, 'text/plain') #application/docbook+xml


