# -*- coding: utf-8 -*-

import re

from reportlab.lib import pagesizes, units, enums
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import registerTypeFace, registerFont, \
                                         TypeFace
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus.frames import Frame, ShowBoundaryValue
from reportlab.platypus.flowables import PageBreak
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate, \
                                           FrameBreak

from trac.util.datefmt import format_datetime, pretty_timedelta
from trac.util.translation import dgettext

import tracstickyticket

__all__ = ['PdfStickyTicket']

class PdfStickyTicket(object):
    _stdfonts = (
        'Courier', 'Courier-Bold', 'Courier-Oblique', 'Courier-BoldOblique',
        'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique',
        'Helvetica-BoldOblique', 'Times-Roman', 'Times-Bold', 'Times-Italic',
        'Times-BoldItalic', 'Symbol','ZapfDingbats',
    )
    _cidfonts = (
        'STSong-Light',
        'MSung-Light', 'MHei-Medium',
        'HeiseiMin-W3', 'HeiseiKakuGo-W5',
        'HYSMyeongJo-Medium','HYGothic-Medium',
    )

    def __init__(self, filename, tickets, pagesize='A4',
                 stickysize=(75, 75), fontname='(auto)', locale=None):
        self.filename = filename
        self.tickets = tickets
        self.pagesize = self._get_pagesize(pagesize)
        self.stickysize = [units.toLength('%gmm' % val) for val in stickysize]
        self.locale = locale
        self.fontname = self._setup_font(fontname, locale)

    def generate(self):
        tickets = self.tickets
        show_boundary = (False, True)[len(tickets) == 0]
        elements = []

        doc = StickyDocument(self.filename, self.pagesize, self.stickysize,
                             show_boundary=show_boundary)
        count = doc.cols * doc.rows

        if tickets:
            styles = {
                'main': ParagraphStyle('sticky-main', firstLineIndent=0,
                                       fontSize=12, autoLeading='max',
                                       keepWithNext=0, wordWrap='CJK'),
            }
            styles['type'] = ParagraphStyle('sticky-type',
                                            parent=styles['main'],
                                            alignment=enums.TA_RIGHT)
            framebreak = FrameBreak()
            pagebreak = PageBreak()
            for idx, ticket in enumerate(tickets):
                if idx != 0:
                    if idx % count == 0:
                        elements.append(pagebreak)
                    else:
                        elements.append(framebreak)
                elements.extend((
                    self._create_element_type(ticket, styles['type']),
                    framebreak,
                    self._create_element_main(ticket, styles['main']),
                ))
        else:
            elements.extend([FrameBreak()] * (count * 2 - 1))
        doc.build(elements)

    def _setup_font(self, fontname, locale):
        registerTypeFace(TypeFace('Times-Roman'))

        if fontname != '(auto)':
            if fontname not in self._stdfonts \
                    and fontname not in self._cidfonts:
                fontname = '(auto)'

        if fontname == '(auto)':
            fontname = 'Helvetica'
            if not locale:
                pass
            if locale == 'ja':
                fontname = 'HeiseiKakuGo-W5'
            elif locale == 'ko':
                fontname = 'HYGothic-Medium'
            elif locale.startswith('zh_'):
                fontname = 'STSong-Light'

        if fontname in self._stdfonts:
            font = TypeFace(fontname)
            registerTypeFace(font)
        elif fontname in self._cidfonts:
            font = UnicodeCIDFont(fontname)
            registerFont(font)

        return fontname

    def _create_element_type(self, ticket, style):
        data = {
            'fontname': _escape(self.fontname),
            'type': _escape(ticket['type']),
        }
        text = '<font name="%(fontname)s" size="14">%(type)s</font>' % data
        return Paragraph(text, style)

    def _create_element_main(self, ticket, style):
        time = ticket['time']
        data = dict((key, _escape(val)) for key, val in ticket.iteritems())
        data['time'] = format_datetime(time, '%Y-%m-%d %H:%M')
        data['dateinfo'] = pretty_timedelta(time)
        data['fontname'] = _escape(self.fontname)
        data['label_reporter'] = _escape(dgettext('messages', ('Reporter')))
        data['label_time'] = _escape(dgettext('messages', ('Created')))

        text = '<font name="Helvetica" size="36">' \
               '<b>#%(id)d</b></font><br/>' \
               '<br/>' \
               '<font name="%(fontname)s" size="12">' \
               '<b>%(summary)s</b></font><br/>' \
               '<br/>' \
               '<font name="%(fontname)s" size="10.5">' \
               '%(label_reporter)s: %(reporter)s<br/>' \
               '%(label_time)s: %(time)s (%(dateinfo)s)' \
               '</font>' % data

        return Paragraph(text, style)

    def _get_pagesize(self, name):
        name = name.strip().upper()
        if hasattr(pagesizes, name):
            size = getattr(pagesizes, name)
            if isinstance(size, (list, tuple)) and len(size) == 2:
                return size
        return getattr(pagesizes, 'A4')

class StickyDocument(BaseDocTemplate):
    def __init__(self, filename, pagesize, stickysize, show_boundary=False):
        self.cols = int(pagesize[0] // stickysize[0])
        self.rows = int(pagesize[1] // stickysize[1])

        templates = [
            StickyPage('sticky-page', pagesize, stickysize, self.cols,
                       self.rows, show_boundary),
        ]
        BaseDocTemplate.__init__(self, filename, pageTemplates=templates,
                                 allowSplitting=0, creator=self._get_creator())

    def _get_creator(self):
        name = tracstickyticket.NAME
        version = tracstickyticket.VERSION
        return '%(name)s-%(version)s' % locals()

class StickyPage(PageTemplate):
    def __init__(self, id, pagesize, stickysize, cols, rows, show_boundary):
        margin_h = (pagesize[0] - stickysize[0] * cols) / (cols + 1)
        margin_v = (pagesize[1] - stickysize[1] * rows) / (rows + 1)

        if show_boundary:
            boundary = ShowBoundaryValue((0, 0, 0), 0.3)
        else:
            boundary = ShowBoundaryValue((0.75, 0.75, 0.75), 0.05)

        frames = []
        for ridx in xrange(rows):
            for cidx in xrange(cols):
                frame_type = Frame(
                    x1=cidx * (margin_h + stickysize[0]) + margin_h,
                    y1=pagesize[1] - (ridx + 1) * (margin_v + stickysize[1]),
                    width=stickysize[0],
                    height=stickysize[1],
                    leftPadding=12,
                    bottomPadding=12,
                    rightPadding=8,
                    topPadding=8,
                    showBoundary=0,
                )
                frame_main = Frame(
                    x1=cidx * (margin_h + stickysize[0]) + margin_h,
                    y1=pagesize[1] - (ridx + 1) * (margin_v + stickysize[1]),
                    width=stickysize[0],
                    height=stickysize[1],
                    leftPadding=12,
                    bottomPadding=12,
                    rightPadding=16,
                    topPadding=8,
                    showBoundary=boundary,
                )
                frames.append(frame_type)
                frames.append(frame_main)

        PageTemplate.__init__(self, id=id, frames=frames, pagesize=pagesize)

_escape_tab = {'&': '&amp;', '<': '&lt;', '>': '&gt;'}
_escape_re = re.compile(r'[&<>]', re.U)

def _escape(val):
    if not isinstance(val, basestring):
        return val
    def replace(match):
        return _escape_tab[match.group(0)]
    return _escape_re.sub(replace, val)
