# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Matthew Good <matt@matt-good.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# Author: Matthew Good <matt@matt-good.net>
"""Syntax highlighting based on Pygments."""

from datetime import datetime
import os
from pkg_resources import resource_filename
import re
import time

from trac.core import *
from trac.config import ListOption, Option
from trac.mimeview.api import IHTMLPreviewRenderer, Mimeview
from trac.wiki.api import IWikiMacroProvider
from trac.util.datefmt import http_date
from trac.util.html import Markup
from trac.web import IRequestHandler, IRequestFilter
from trac.web.chrome import add_link, ITemplateProvider

try:
    import pygments
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters.html import HtmlFormatter
    from pygments.styles import get_style_by_name
    have_pygments = True
except ImportError, e:
    have_pygments = False
else:
    have_pygments = True

__all__ = ['PygmentsRenderer']


class PygmentsRenderer(Component):
    """Syntax highlighting based on Pygments."""

    implements(IHTMLPreviewRenderer, IRequestHandler, IRequestFilter,
               IWikiMacroProvider, ITemplateProvider)

    default_style = Option('mimeviewer', 'pygments_default_style', 'trac',
        """The default style to use for Pygments syntax highlighting.""")

    pygments_modes = ListOption('mimeviewer', 'pygments_modes',
        '', doc=
        """List of additional MIME types known by Pygments.

        For each, a tuple `mimetype:mode:quality` has to be
        specified, where `mimetype` is the MIME type,
        `mode` is the corresponding Pygments mode to be used
        for the conversion and `quality` is the quality ratio
        associated to this conversion. That can also be used
        to override the default quality ratio used by the
        Pygments render.""")

    expand_tabs = True
    returns_source = True

    QUALITY_RATIO = 7

    EXAMPLE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Hello, world!</title>
    <script>
      $(document).ready(function() {
        $("h1").fadeIn("slow");
      });
    </script>
  </head>
  <body>
    <h1>Hello, world!</h1>
  </body>
</html>"""

    def __init__(self):
        self.log.debug("Pygments installed? %r", have_pygments)
        if have_pygments:
            version = getattr(pygments, '__version__', None)
            if version:
                self.log.debug('Pygments Version: %s' % version)

        self._types = None

    # IHTMLPreviewRenderer implementation

    def get_quality_ratio(self, mimetype):
        # Extend default MIME type to mode mappings with configured ones
        self._init_types()
        try:
            return self._types[mimetype][1]
        except KeyError:
            return 0

    def render(self, req, mimetype, content, filename=None, rev=None):
        self._init_types()
        try:
            mimetype = mimetype.split(';', 1)[0]
            language = self._types[mimetype][0]
            return self._highlight(language, content, True)
        except (KeyError, ValueError):
            raise Exception("No Pygments lexer found for mime-type '%s'."
                            % mimetype)

    # IWikiMacroProvider implementation

    def get_macros(self):
        self._init_types()
        return self._languages.keys()

    def get_macro_description(self, name):
        self._init_types()
        return 'Syntax highlighting for %s using Pygments' % self._languages[name]

    def render_macro(self, req, name, content):
        self._init_types()
        return self._highlight(name, content, False)

    # IRequestFilter
    
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, content_type):
        if not getattr(req, '_no_pygments_stylesheet', False):
            add_link(req, 'stylesheet', self.env.href('pygments', '%s.css' %
                     req.session.get('pygments_style', self.default_style)))
        return template, content_type

    # IRequestHandler implementation

    def match_request(self, req):
        if have_pygments:
            if re.match(r'/pygments/?$', req.path_info):
                return True
            match = re.match(r'/pygments/(\w+)\.css$', req.path_info)
            if match:
                try:
                    req.args['style'] = get_style_by_name(match.group(1))
                except ValueError:
                    return False
                return True
        return False

    def process_request(self, req):
        # settings panel
        if not 'style' in req.args:
            req._no_pygments_stylesheet = True
            styles = list(get_all_styles())
            styles.sort(lambda a, b: cmp(a.lower(), b.lower()))

            if req.method == 'POST':
                style = req.args.get('new_style')
                if style and style in styles:
                    req.session['pygments_style'] = style

            output = self._highlight('html', self.EXAMPLE, False)
            req.hdf['output'] = Markup(output)
            req.hdf['current'] = req.session.get('pygments_style',
                                                 self.default_style)
            req.hdf['styles'] = styles
            req.hdf['pygments_path'] = self.env.href.pygments()
            return 'pygments_settings.cs', None

        # provide stylesheet
        else:
            style = req.args['style']

            parts = style.__module__.split('.')
            filename = resource_filename('.'.join(parts[:-1]), parts[-1] + '.py')
            mtime = datetime.utcfromtimestamp(os.path.getmtime(filename))
            last_modified = http_date(time.mktime(mtime.timetuple()))
            if last_modified == req.get_header('If-Modified-Since'):
                req.send_response(304)
                req.end_headers()
                return

            formatter = HtmlFormatter(style=style)
            content = u'\n\n'.join([
                formatter.get_style_defs('div.code pre'),
                formatter.get_style_defs('table.code td')
            ]).encode('utf-8')

            req.send_response(200)
            req.send_header('Content-Type', 'text/css; charset=utf-8')
            req.send_header('Last-Modified', last_modified)
            req.send_header('Content-Length', len(content))
            req.write(content)

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return ()

    # Internal methods

    def _init_types(self):
        if self._types is None:
            self._types = {}
            self._languages = {}
            if have_pygments:
                for name, aliases, _, mimetypes in get_all_lexers():
                    for mimetype in mimetypes:
                        self._types[mimetype] = (aliases[0], self.QUALITY_RATIO)
                    for alias in aliases:
                        self._languages[alias] = name
                self._types.update(
                    Mimeview(self.env).configured_modes_mapping('pygments')
                )

    def _highlight(self, language, content, annotate):
        formatter = HtmlFormatter(cssclass=not annotate and 'code' or '')
        html = pygments.highlight(content, get_lexer_by_name(language),
                                  formatter).rstrip('\n')
        if annotate:
            return html[len('<div><pre>'):-len('</pre></div>')].splitlines()
        return html


def get_all_lexers():
    from pygments.lexers._mapping import LEXERS
    from pygments.plugin import find_plugin_lexers

    for item in LEXERS.itervalues():
        yield item[1:]
    for cls in find_plugin_lexers():
        yield cls.name, cls.aliases, cls.filenames, cls.mimetypes


def get_all_styles():
    from pygments.styles import find_plugin_styles, STYLE_MAP
    for name in STYLE_MAP:
        yield name
    for name, _ in find_plugin_styles():
        yield name
