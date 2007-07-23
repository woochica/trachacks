from trac.wiki.formatter import Formatter
from trac.util.html import escape
from StringIO import StringIO
import os

class OpenDocumentFormatter(Formatter):
    def __init__(self, env, req=None, absurls=False, db=None, styles=None):
        Formatter.__init__(self, env, req=None, absurls=False, db=None)
        self.styles = styles
        self._in_list_item = False

    def get_style(self, style):
        try:
            return self.styles[style]
        except:
            raise
            return self.styles['standard']

    def simple_span_handler(self, text, style):
        return self.simple_tag_handler(text,
            '<text:span text:style-name="%s">' % self.get_style(style),
            '</text:span>')

    def p(self, style):
        if style is None:
            return "<text:p>"
        return "<text:p text:style-name='%s'>" % self.get_style(style)

    def open_paragraph(self, style='standard'):
        if not self.paragraph_open:
            self.out.write(self.p(style))
            self.paragraph_open = 1

    def close_paragraph(self):
        if self.paragraph_open:
            while self._open_tags != []:
                self.out.write(self._open_tags.pop()[1])
            self.out.write('</text:p>' + os.linesep)
            self.paragraph_open = 0

    def _heading_formatter(self, match, fullmatch):
        self.close_table()
        self.close_paragraph()
        self.close_indentation()
        self.close_list()
        self.close_def_list()
        depth, heading, anchor = self._parse_heading(match, fullmatch, False)
        self.out.write('<text:p text:style-name="%s" id="%s">%s</text:p>' %
                       (self.get_style('heading_%s' % depth), anchor, heading))



    def _set_list_depth(self, depth, new_type, list_class, start):
        def open_item():
            list_type = new_type == 'ol' and 'ordered' or 'unordered'
            style = '%s_list' % ( list_type )
            self.out.write('<text:list-item>')
            self.open_paragraph(None)
        def close_item():
            self.close_paragraph()
            self.out.write('</text:list-item>')
        def open_list():
            self.close_table()
            self.close_paragraph()
            self.close_indentation() # FIXME: why not lists in quotes?
            self._list_stack.append((new_type, depth))
            self._set_tab(depth)
            list_type = new_type == 'ol' and 'ordered' or 'unordered'
            self.out.write('<text:list text:style-name="%s">' % (
                    self.get_style('%s_list' % (
                        list_type))))
            open_item()

        def close_list(tp):
            self._list_stack.pop()
            close_item()
            self.out.write('</text:list>')

        # depending on the indent/dedent, open or close lists
        if depth > self._get_list_depth():
            open_list()
        else:
            while self._list_stack:
                deepest_type, deepest_offset = self._list_stack[-1]
                if depth >= deepest_offset:
                    break
                close_list(deepest_type)
            if depth > 0:
                if self._list_stack:
                    old_type, old_offset = self._list_stack[-1]
                    if new_type and old_type != new_type:
                        close_list(old_type)
                        open_list()
                    else:
                        if old_offset != depth: # adjust last depth
                            self._list_stack[-1] = (old_type, depth)
                        close_item()
                        open_item()
                else:
                    open_list()

    def _bold_formatter(self, match, fullmatch):
        return self.simple_span_handler(match, 'bold')

    def _italic_formatter(self, match, fullmatch):
        return self.simple_span_handler(match, 'italic')

    def _bolditalic_formatter(self, match, fullmatch):
        return self.simple_span_handler(match, 'bolditalic')

    def _inlinecode_formatter(self, match, fullmatch):
        return '<text:span text:style-name="%s">%s</text:span>' % (
            self.get_style('inline'), escape(fullmatch.group('inline')))

    def _inlinecode2_formatter(self, match, fullmatch):
        return '<text:span text:style-name="%s">%s</text:span>' % (
            self.get_style('inline'), escape(fullmatch.group('inline2')))

    def _make_ext_link(self, url, text, title=''):
    	return '<text:a xlink:href="%s"%s>%s</text:a>' % (
		url, title and 'office:name="%s"' % title or '', text)

def wiki_to_odt(wikitext, env, req, styles,
    db=None, absurls=False, escape_newlines=False):
    out = StringIO()
    OpenDocumentFormatter(env, req, absurls, db, styles).format(wikitext, out, escape_newlines)
    return '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
    xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
    xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
    xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
    xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
    xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
    xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0"
    xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0"
    xmlns:math="http://www.w3.org/1998/Math/MathML"
    xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0"
    xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0"
    xmlns:ooo="http://openoffice.org/2004/office"
    xmlns:ooow="http://openoffice.org/2004/writer"
    xmlns:oooc="http://openoffice.org/2004/calc"
    xmlns:dom="http://www.w3.org/2001/xml-events"
    xmlns:xforms="http://www.w3.org/2002/xforms"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    office:version="1.0">
  <office:body>
    <office:text>
''' + out.getvalue().encode('utf-8') + '''
    </office:text>
  </office:body>
</office:document-content>
'''


