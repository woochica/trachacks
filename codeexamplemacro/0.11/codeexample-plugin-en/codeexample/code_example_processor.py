# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Alexander Slesarev <nuald@codedgers.com>.
# All rights reserved by Codedgers Inc (http://codedgers.com).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Code example processor module. """

import re
from trac.wiki.macros import IWikiMacroProvider
from trac.core import implements, Component
from trac.util.text import to_unicode
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome, \
    Markup, add_script
from trac.config import Option

try:
    __import__('pygments', {}, {}, [])
    HAVE_PYGMENTS = True
except ImportError:
    HAVE_PYGMENTS = False

if HAVE_PYGMENTS:
    from pygments.lexers import get_lexer_by_name
    from trac.mimeview.pygments import GenshiHtmlFormatter
    from pygments.util import ClassNotFound

__all__ = ['CodeExample']


class CodeExample(Component):
    """ Code example macro class. """

    implements(ITemplateProvider, IWikiMacroProvider)

    styles = {
        'CodeExample': {'title': u'EXAMPLE', 'css_class': 'example'},
        'BadCodeExample': {'title': u'INCORRECT EXAMPLE',
                           'css_class': 'bad_example'},
        'GoodCodeExample': {'title': u'CORRECT EXAMPLE',
                            'css_class': 'good_example'}}

    default_style = Option('mimeviewer', 'pygments_default_style', 'trac',
        """The default style to use for Pygments syntax highlighting.""")

    def __init__(self):
        super(CodeExample, self).__init__()
        self._render_exceptions = []
        self._index = 0

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        for key in sorted(self.styles.keys()):
            yield key

    def render_as_lang(self, lang, content):
        """ Try to render 'content' as 'lang' code. """
        try:
            lexer = get_lexer_by_name(lang, stripnl = False)
            tokens = lexer.get_tokens(content)
            stream = GenshiHtmlFormatter().generate(tokens)
            return stream.render(strip_whitespace = False)
        except ClassNotFound, exception:
            self._render_exceptions.append(exception)
        return content

    def pygmentize_args(self, args, have_pygments):
        """ Process args via Pygments. """
        if have_pygments:
            match = re.match('^#!(.+)\s*\n((.*\s*)*)$', args, re.MULTILINE)
            if match:
                args = self.render_as_lang(match.group(1), match.group(2))
        return args

    @staticmethod
    def get_templates_dirs():
        """ Notify Trac about templates dir. """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    @staticmethod
    def get_htdocs_dirs():
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('ce', resource_filename(__name__, 'htdocs'))]

    @staticmethod
    def is_have_pygments():
        return HAVE_PYGMENTS

    def expand_macro(self, formatter, name, args):
        """ Expand macro parameters and return required html. """
        self._render_exceptions = []
        self._index += 1
        add_stylesheet(formatter.req, '/pygments/%s.css' %
                       formatter.req.session.get('pygments_style',
                                                 self.default_style))
        add_script(formatter.req, 'ce/js/select_code.js')
        add_stylesheet(formatter.req, 'ce/css/codeexample.css')
        args = to_unicode(self.pygmentize_args(args, HAVE_PYGMENTS))
        data = self.styles[name]
        data.update({'args': Markup(args)})
        data.update({'exceptions': self._render_exceptions})
        data.update({'index': self._index})
        req = formatter.req
        return Chrome(self.env).render_template(req, 'codeexample.html', data,
            None, fragment=True).render(strip_whitespace = False)
