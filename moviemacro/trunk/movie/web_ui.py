# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.mimeview.api import IHTMLPreviewRenderer
from trac.wiki.formatter import format_to_html

class MoviePreviewRenderer(Component):

    implements(IHTMLPreviewRenderer)

    ### IHTMLPreviewRenderer methods

    def get_quality_ratio(self, mimetype):
        if mimetype.startswith('video/'):
            return 9
        return 0

    def render(self, context, mimetype, content, filename=None, url=None):
        return format_to_html(self.env, context, '[[Movie(%s)]]' % url)

