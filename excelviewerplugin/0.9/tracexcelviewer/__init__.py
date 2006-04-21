# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.

from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer
from trac.util import escape

__all__ = ['ExcelRenderer']

try:
    import xlrd
    have_xrld = True
except ImportError:
    have_xrld = False


class ExcelRenderer(Component):
    """Syntax highlighting using GNU Enscript."""

    implements(IHTMLPreviewRenderer)

    MIME_TYPES = ('application/vnd.ms-excel', 'application/excel')

    # IHTMLPreviewRenderer methods

    def get_quality_ratio(self, mimetype):
        if have_xrld and mimetype in self.MIME_TYPES:
            return 2
        return 0

    def render(self, req, mimetype, content, filename=None, url=None):
        if hasattr(content, 'read'):
            content = content.read()
        book = xlrd.open_workbook(file_contents=content)
        buf = []
        for sheet_name in book.sheet_names():
            sheet = book.sheet_by_name(sheet_name)
            buf.append(u'<table class="listing"><caption>%s</caption>\n' %
                       escape(sheet.name))
            buf.append(u'<tbody>')
            for ridx in range(sheet.nrows):
                row = sheet.row(ridx)
                if not filter(lambda cell: unicode(cell.value), row):
                    continue
                buf.append(u'<tr class="%s">' % (ridx % 2 and 'odd' or 'even'))
                for cidx, cell in enumerate(row):
                    buf.append(u'<td>%s</td>' % sheet.cell_value(ridx, cidx))
                buf.append(u'</tr>\n')
            buf.append(u'</tbody>')
            buf.append(u'</table>\n')
        return u''.join(buf)
