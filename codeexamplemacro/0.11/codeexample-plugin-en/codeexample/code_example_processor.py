# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Alexander Slesarev <nuald@codedgers.com>.
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
import os.path
from trac.wiki.macros import IWikiMacroProvider
from trac.core import implements, Component, TracError
from trac.util.text import to_unicode
from trac.versioncontrol.api import NoSuchNode, RepositoryManager
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
        'CodeExample': {'title': u'EXAMPLE', 'css_class': 'example',
                'description': 'Render the code block as a plain example.'},
        'BadCodeExample': {'title': u'INCORRECT EXAMPLE',
                           'css_class': 'bad_example',
                'description': 'Render the code block as a bad example.'},
        'GoodCodeExample': {'title': u'CORRECT EXAMPLE',
                            'css_class': 'good_example',
                'description': 'Render the code block as a good example.'},
        'CodeExamplePath': {'title': u'EXAMPLE', 'css_class': 'example',
        'description': 'Render the code from the path as a plain example.'},
        'BadCodeExamplePath': {'title': u'INCORRECT EXAMPLE',
                           'css_class': 'bad_example',
        'description': 'Render the code from the path as a bad example.'},
        'GoodCodeExamplePath': {'title': u'CORRECT EXAMPLE',
                            'css_class': 'good_example',
        'description': 'Render the code from the path as a good example.'},
}

    default_style = Option('mimeviewer', 'pygments_default_style', 'trac',
        """The default style to use for Pygments syntax highlighting.""")

    def __init__(self):
        super(CodeExample, self).__init__()
        self._render_exceptions = []
        self._index = 0
        self._link = None

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        for key in sorted(self.styles.keys()):
            yield key

    def get_macro_description(self, name):
        """Returns the required macro description."""
        return self.styles[name]['description']

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

    def get_analyzed_content(self, text, required_lines):
        """ Strip text for required lines. """
        lines = list(enumerate(text.split('\n')))
        if required_lines:
            lines_range = self.get_range(required_lines)
            lines = filter(lambda i: i[0] + 1 in lines_range, lines)
        return lines

    def get_quote(self, text, args, required_lines=None, focus_line=None):
        """ Try to get the required quote from the text. """
        regex_match = re.search('^\s*regex\s*=\s*"?(.+?)"?\s*$',
                                   args, re.MULTILINE)
        lines_match = re.search('^\s*lines\s*=\s*(\d+)\s*$',
                                   args, re.MULTILINE)
        begin_idx = 0
        content = self.get_analyzed_content(text, required_lines)
        if regex_match:
            regex = regex_match.group(1)
            for begin_idx, s in list(enumerate(content)):
                if re.search(regex, s[1]):
                    break
            else:
                err = 'Nothing is match to regex: ' + regex
                self._render_exceptions.append(err)
                begin_idx = 0
        if begin_idx and self._link and not focus_line:
            self._link += "#L%d" % (list(content)[begin_idx][0] + 1)
        if self._link and focus_line:
            self._link += "#L%d" % focus_line
        simple_content = [i[1] for i in content]
        if lines_match:
            lines = int(lines_match.group(1))
            return '\n'.join(simple_content[begin_idx:lines + begin_idx])
        else:
            return '\n'.join(simple_content[begin_idx:])

    def get_repos_manager(self):
        """ Get repository manager. """
        return RepositoryManager(self.env)

    def parse_path(self, path):
        """ Parse source path. """
        path_match = re.search(
            '^\s*path\s*=\s*(?P<path>.+?)(?P<rev>@\w+)?' \
            '(?P<lines>:\d+(-\d+)?(,\d+(-\d+)?)*)?(?P<focus>#L\d+)?\s*$',
            path, re.MULTILINE)
        if path_match:
            path = path_match.group('path')
            rev = path_match.group('rev')
            if rev:
                rev = rev[1:]
            lines = path_match.group('lines')
            if lines:
                lines = lines[1:]
            focus_line = path_match.group('focus')
            if focus_line:
                focus_line = int(focus_line[2:])
            return path, rev, lines, focus_line
        return None, None, None, None

    @staticmethod
    def get_range(lines):
        """ Get range from lines string. """
        groups = lines.split(',')
        lines_range = set()
        for group in groups:
            numbers = group.strip().split('-')
            if len(numbers) == 2:
                num1, num2 = numbers
                lines_range |= set(range(int(num1), int(num2) + 1))
            else:
                lines_range.add(int(numbers[0]))
        return sorted(lines_range)

    def get_sources(self, src):
        """ Try to get sources from the required path. """
        try:
            repo_mgr = self.get_repos_manager()
            repos = repo_mgr.get_repository(None)
        except TracError, exception:
            self._render_exceptions.append(exception)
            return src
        try:
            path, rev, lines, focus_line = self.parse_path(src)
            if path:
                try:
                    node = repos.get_node(path, rev)
                    self._link = self.env.href.browser(node.path)
                    stream = node.get_content()
                    src = self.get_quote(to_unicode(stream.read()), src, lines,
                                     focus_line)
                except NoSuchNode, exception:
                    self._render_exceptions.append(exception)
            else:
                self._render_exceptions.append('Path element is not found.')
        finally:
            repo_mgr.shutdown()
        return src

    def actualize(self, src, is_path):
        """ Detect and load required sources. """
        if is_path:
            return self.get_sources(src)
        return src

    def pygmentize_args(self, args, have_pygments, is_path):
        """ Process args via Pygments. """
        if have_pygments:
            match = re.match('^#!(.+?)\s+((.*\s*)*)$', args, re.MULTILINE)
            if match:
                return self.render_as_lang(match.group(1),
                                       self.actualize(match.group(2), is_path))
        return self.actualize(args, is_path)

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
        return [('ce', os.path.abspath(resource_filename(__name__, 'htdocs')))]

    @staticmethod
    def is_have_pygments():
        return HAVE_PYGMENTS

    def expand_macro(self, formatter, name, args):
        """ Expand macro parameters and return required html. """
        self._render_exceptions = []
        self._link = None
        self._index += 1
        add_stylesheet(formatter.req, '/pygments/%s.css' %
                       formatter.req.session.get('pygments_style',
                                                 self.default_style))
        add_script(formatter.req, 'ce/js/select_code.js')
        add_stylesheet(formatter.req, 'ce/css/codeexample.css')
        is_path = name[-4:] == 'Path'
        args = to_unicode(self.pygmentize_args(args, HAVE_PYGMENTS, is_path))
        data = self.styles[name]
        data.update({'args': Markup(args)})
        data.update({'exceptions': self._render_exceptions})
        data.update({'index': self._index})
        data.update({'link': self._link})
        req = formatter.req
        return Chrome(self.env).render_template(req, 'codeexample.html', data,
            None, fragment=True).render(strip_whitespace = False)
