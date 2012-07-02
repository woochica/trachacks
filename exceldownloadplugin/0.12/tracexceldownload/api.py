# -*- coding: utf-8 -*-

import os
import re
from datetime import datetime
from tempfile import mkstemp
from unicodedata import east_asian_width
from xlwt import XFStyle, Style, Alignment, Borders, Pattern, Font

from trac.util.text import to_unicode


class WorksheetWriter(object):

    def __init__(self, sheet, req):
        self.sheet = sheet
        self.req = req
        self.tz = req.tz
        if hasattr(req, 'locale'):
            self.ambiwidth = (1, 2)[str(req.locale)[:2] in ('ja', 'kr', 'zh')]
        else:
            self.ambiwidth = 1
        self.styles = self._get_excel_styles()
        self.row_idx = 0
        self._col_widths = {}
        self._metrics_cache = {}

    def write_row(self, cells):
        row = self.sheet.row(self.row_idx)
        max_line = 1
        max_height = 0
        for idx, (value, style, width, line) in enumerate(cells):
            if isinstance(value, datetime):
                value = value.astimezone(self.tz)
                if hasattr(self.tz, 'normalize'): # pytz
                    value = self.tz.normalize(value)
                value = datetime(*(value.timetuple()[0:6]))
                if style == '[date]':
                    width = len('YYYY-MM-DD')
                elif style == '[time]':
                    width = len('HH:MM:SS')
                else:
                    width = len('YYYY-MM-DD HH:MM:SS')
                line = 1
            if width is None or line is None:
                metrics = self.get_metrics(value)
                if width is None:
                    width = metrics[0]
                if line is None:
                    line = metrics[1]
            if width >= 0:
                self._col_widths.setdefault(idx, 0)
                if self._col_widths[idx] < width:
                    self._col_widths[idx] = width
            if line >= 0 and max_line < line:
                max_line = line
            if isinstance(style, basestring):
                if style not in self.styles:
                    style = ('*', '*:change')[style.endswith(':change')]
                style = self.styles[style]
            if max_height < style.font.height:
                max_height = style.font.height
            row.write(idx, value, style)
        row.height = min(max_line, 10) * max(max_height * 255 / 180, 255)
        row.height_mismatch = True
        self.row_idx += 1

    def set_col_widths(self):
        for idx, width in self._col_widths.iteritems():
            self.sheet.col(idx).width = (1 + min(width, 50)) * 256

    _NORMALIZE_NEWLINE = re.compile(r'\r\n?').sub

    def get_metrics(self, value):
        value = self._NORMALIZE_NEWLINE('\n', to_unicode(value)).strip()
        if not value:
            return 0, 1
        if value not in self._metrics_cache:
            lines = value.splitlines()
            doubles = ('WFA', 'WF')[self.ambiwidth == 1]
            width = max(sum((1, 2)[east_asian_width(ch) in doubles]
                            for ch in line)
                        for line in lines)
            self._metrics_cache[value] = (width, len(lines))
        return self._metrics_cache[value]

    def _get_excel_styles(self):
        def style_base():
            style = XFStyle()
            style.alignment.vert = Alignment.VERT_TOP
            style.alignment.wrap = True
            style.font.height = 180 # 9pt
            borders = style.borders
            borders.left = Borders.THIN
            borders.right = Borders.THIN
            borders.top = Borders.THIN
            borders.bottom = Borders.THIN
            return style

        header = XFStyle()
        header.font.height = 400 # 20pt
        header2 = XFStyle()
        header2.font.height = 320 # 16pt

        thead = style_base()
        thead.font.bold = True
        thead.font.colour_index = Style.colour_map['white']
        thead.pattern.pattern = Pattern.SOLID_PATTERN
        thead.pattern.pattern_fore_colour = Style.colour_map['black']
        thead.borders.colour = 'white'
        thead.borders.left = Borders.THIN
        thead.borders.right = Borders.THIN
        thead.borders.top = Borders.THIN
        thead.borders.bottom = Borders.THIN

        def style_change(style):
            pattern = style.pattern
            pattern.pattern = Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = Style.colour_map['light_orange']
            return style

        def style_id():
            style = style_base()
            style.font.underline = Font.UNDERLINE_SINGLE
            style.font.colour_index = Style.colour_map['blue']
            style.num_format_str = '"#"0'
            return style

        def style_milestone():
            style = style_base()
            style.font.underline = Font.UNDERLINE_SINGLE
            style.font.colour_index = Style.colour_map['blue']
            style.num_format_str = '@'
            return style

        def style_time():
            style = style_base()
            style.num_format_str = 'HH:MM:SS'
            return style

        def style_date():
            style = style_base()
            style.num_format_str = 'YYYY-MM-DD'
            return style

        def style_datetime():
            style = style_base()
            style.num_format_str = 'YYYY-MM-DD HH:MM:SS'
            return style

        def style_default():
            style = style_base()
            style.num_format_str = '@'    # String
            return style

        styles = {'header': header, 'header2': header2, 'thead': thead}
        for key, func in (('id', style_id),
                          ('milestone', style_milestone),
                          ('[time]', style_time),
                          ('[date]', style_date),
                          ('[datetime]', style_datetime),
                          ('*', style_default)):
            styles[key] = func()
            styles['%s:change' % key] = style_change(func())
        return styles


def get_workbook_content(book):
    f = None
    fd, path = mkstemp()
    try:
        book.save(path)
        f = os.fdopen(fd)
        return f.read()
    finally:
        if f is None:
            os.close(fd)
        else:
            f.close()
        os.unlink(path)


def get_literal(text):
    return u'"%s"' % to_unicode(text).replace('"', '""')
