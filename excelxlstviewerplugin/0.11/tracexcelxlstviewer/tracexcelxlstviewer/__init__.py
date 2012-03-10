# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Daniel Rolls, Maxeler Technologies Inc <drolls@maxeler.com>  
# Derived from Christopher Lenz's ExcelViewerPlugin 
#   Copyright (C) 2006 Christopher Lenz <cmlenz@gmx.de>
#   All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer
from trac.util import escape
import tempfile, os

__all__ = ['ExcelXSLTRenderer']

try:
    import openpyxl
    have_openpyxl = True
except ImportError:
    have_openpyxl = False


class ExcelXSLTRenderer(Component):
    implements(IHTMLPreviewRenderer)

    MIME_TYPES = ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
		  'application/vnd.ms-excel.sheet.macroEnabled.12')

    # IHTMLPreviewRenderer methods

    def get_quality_ratio(self, mimetype):
        if have_openpyxl and mimetype in self.MIME_TYPES:
            return 2
        return 0

    def render(self, req, mimetype, content, filename=None, url=None):
        if hasattr(content, 'read'):
            content = content.read()
	fd, path = tempfile.mkstemp(suffix='.xlsx', text=True)
	os.write(fd, content)
	os.close(fd)
	book = openpyxl.load_workbook(path)
        buf = []
	for sheetName in book.get_sheet_names():
	    sheet = book.get_sheet_by_name(sheetName)
	    if len(sheet.get_cell_collection()) == 0:
	        continue # Skip empty sheet
	    buf.append(u'<table class="listing"><caption>%s</caption>\n' % escape(sheetName))
            buf.append(u'<tbody>')
	    sheet.get_highest_row()
	    rowIdx = 0
	    for row in sheet.range(sheet.calculate_dimension()):
                buf.append(u'<tr class="%s">' % (rowIdx % 2 and 'odd' or 'even'))
		for cell in row:
		    if cell.value == None:
		        val = u''
	            else:
		        val = cell.value
                    buf.append(u'<td>%s</td>' % val)
                buf.append(u'</tr>\n')
		rowIdx = rowIdx + 1
            buf.append(u'</tbody>')
            buf.append(u'</table>\n')
	os.unlink(path)
        return u''.join(buf)

