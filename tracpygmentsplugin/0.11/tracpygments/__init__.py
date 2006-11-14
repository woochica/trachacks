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

"""Syntax highlighting module, based on the Pygments module.
"""

import re
from StringIO import StringIO

from trac.core import *
from trac.config import ListOption
from trac.mimeview.api import IHTMLPreviewRenderer, Mimeview
from trac.wiki.api import IWikiMacroProvider

__all__ = ['PygmentsRenderer', 'PygmentsProcessors']

try:
    import pygments
    from pygments.lexers._mapping import LEXERS
    from pygments.plugin import find_plugin_lexers
    from pygments.formatters.html import HtmlFormatter
    from pygments.token import *
except ImportError:
    pygments = None

class PygmentsRenderer(Component):
    """Syntax highlighting based on Pygments."""

    implements(IHTMLPreviewRenderer)

    enscript_modes = ListOption('mimeviewer', 'pygments_modes',
        '', doc=
        """List of additional MIME types known by Pygments.
        For each, a tuple `mimetype:mode:quality` has to be
        specified, where `mimetype` is the MIME type,
        `mode` is the corresponding Pygments mode to be used
        for the conversion and `quality` is the quality ratio
        associated to this conversion.
        That can also be used to override the default
        quality ratio used by the Pygments render.""")

    expand_tabs = True

    QUALITY_RATIO = 9

    def __init__(self):
        self._types = None

    def get_quality_ratio(self, mimetype):
        if pygments is None:
            return 0
        # Extend default MIME type to mode mappings with configured ones
        if self._types is None:
            self._types = {}
            for modname, _, aliases, _, mimetypes in _iter_lexerinfo():
                for mimetype in mimetypes:
                    self._types[mimetype] = (aliases[0], self.QUALITY_RATIO)
            self._types.update(
                Mimeview(self.env).configured_modes_mapping('pygments'))
        try:
            return self._types[mimetype][1]
        except KeyError:
            return 0

    def render(self, req, mimetype, content, filename=None, rev=None):
        try:
            mimetype = mimetype.split(';', 1)[0]
            lang = self._types[mimetype][0]
            return _format(lang, content, True)
        except (KeyError, ValueError):
            raise Exception("No Pygments lexer found for mime-type '%s'."
                            % mimetype)


class PygmentsProcessors(Component):
    implements(IWikiMacroProvider)

    def __init__(self):
        self.languages = {}
        try:
            for modname, name, aliases, _, _ in _iter_lexerinfo():
                for alias in aliases:
                    self.languages[alias] = name
        except ImportError:
            pass

    def get_macros(self):
        return self.languages.keys()

    def get_macro_description(self, name):
        return 'Syntax highlighting for %s using Pygments' % self.languages[name]

    def render_macro(self, req, name, content):
        return _format(name, content)


def _iter_lexerinfo():
    for info in LEXERS.itervalues():
        yield info
    for cls in find_plugin_lexers():
        yield cls.__module__, cls.name, cls.aliases, cls.filenames, cls.mimetypes

def _format(lang, content, annotate=False):
    lexer = pygments.get_lexer_by_name(lang)
    formatter = TracHtmlFormatter(cssclass = not annotate and 'code' or '')
    html = pygments.highlight(content, lexer, formatter).rstrip('\n')
    if annotate:
        return html[len('<div><pre>'):-len('</pre></div>')].splitlines()
    else:
        return html

def _issubtoken(token, base):
    while token is not None:
        if token == base:
            return True
        token = token.parent
    return False


if pygments is not None:
    class TracHtmlFormatter(HtmlFormatter):
        # more specific should come before their parents in order to
        # resolve them in the right order
        token_classes = [
            (Comment.Preproc, 'code-prep'),
            (Comment, 'code-comment'),
            (Name.Attribute, 'h_attribute'),
            (Name.Builtin, 'code-lang'),
            (Name.Class, 'code-type'),
            #(Name.Constant, 'code-type'),
            #(Name.Decorator, 'code-type'),
            (Name.Entity, 'h_entity'),
            #(Name.Exception, 'code-type'),
            (Name.Function, 'code-func'),
            #(Name.Label, 'code-type'),
            #(Name.Namespace, 'code-type'),
            (Name.Tag, 'h_tag'),
            (Name.Variable, 'code-var'),
            (Operator, 'code-lang'),
            (String, 'code-string'),
            # TODO String subtokens
            (Keyword.Type, 'code-type'),
            (Keyword, 'code-keyword'),
        ]

        def _get_css_class(self, ttype):
            try:
                return self._class_cache[ttype]
            except KeyError:
                pass
            for token, css_class in self.token_classes:
                if _issubtoken(ttype, token):
                    break
            else:
                css_class = None
            if css_class is not None:
                css_class = self.classprefix + css_class
            self._class_cache[ttype] = css_class
            return css_class
