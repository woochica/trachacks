# -*- coding: utf-8 -*-
""" Test cases for code example processor. """

import unittest
import os.path
import mocker
from mocker import MockerTestCase
from trac.test import EnvironmentStub, Mock
from trac.versioncontrol.api import NoSuchNode
from trac.web.href import Href
from trac.mimeview.api import Context
from trac.wiki.formatter import Formatter
from trac.core import TracError
from codeexample import CodeExample


class CodeExampleTestCase(unittest.TestCase):
    """ Class with test cases for code example processor. """

    def setUp(self):
        """ Set up the testing environment. """
        self.env = EnvironmentStub(enable=[CodeExample])
        self.req = Mock(base_path='', chrome={}, args={},
                        abs_href=Href('/'), href=Href('/'),
                        session={}, perm=[], authname=None,
                        tz=None, locale='utf-8')
        self.context = Context.from_request(self.req)

    def test_get_macros(self):
        """ Testing the get_macros method. """
        processor = CodeExample(self.env)
        expected_result = ['CodeExample']
        index = 0
        for macros in processor.get_macros():
            self.assertEqual(macros, expected_result[index])
            index += 1

    def test_get_macro_description(self):
        """ Testing the get_macro_description method. """
        processor = CodeExample(self.env)
        description = processor.get_macro_description('CodeExample')
        self.assertTrue(len(description) > 0)

    def test_expand_macro_with_unicode(self):
        """ Testing the expand_macro method with unicode symbols. """
        processor = CodeExample(self.env)
        args = 'ТЕСТ'
        formatter = Formatter(self.env, self.context)

        name = 'CodeExample'
        expected = '<div ' \
        'class="example">\n  <div class="title">\n\t' \
        '<span class="select_code" id="link1">' \
        'SELECT ALL</span>\n\t\n\t<span>EXAMPLE:</span>\n</div>\n    \n    ' \
        '<div class="code">' \
        '\n        <pre id="codelink1">ТЕСТ\n</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

    def test_title(self):
        """ Testing the expand_macro method. """
        processor = CodeExample(self.env)
        args = '##title=TITLE\ntest'
        formatter = Formatter(self.env, self.context)

        name = 'CodeExample'
        expected = '<div ' \
        'class="example">\n  <div class="title">\n\t' \
        '<span class="select_code" id="link1">' \
        'SELECT ALL</span>\n\t\n\t<span>TITLE:</span>\n</div>\n    \n    ' \
        '<div class="code">' \
        '\n        <pre id="codelink1">test\n</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

    def test_expand_macro(self):
        """ Testing the expand_macro method. """
        processor = CodeExample(self.env)
        args = 'test'
        formatter = Formatter(self.env, self.context)

        name = 'CodeExample'
        expected = '<div ' \
        'class="example">\n  <div class="title">\n\t' \
        '<span class="select_code" id="link1">' \
        'SELECT ALL</span>\n\t\n\t<span>EXAMPLE:</span>\n</div>\n    \n    ' \
        '<div class="code">' \
        '\n        <pre id="codelink1">test\n</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

        args = '##type=bad\ntest'
        expected = '<div ' \
        'class="bad_example">\n  <div class="title">\n\t' \
        '<span class="select_code" id="link2">' \
        'SELECT ALL</span>\n\t\n\t<span>INCORRECT EXAMPLE:</span>\n' \
        '</div>\n    \n    <div class="code">' \
        '\n        <pre id="codelink2">test\n</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

        args = '##type=good\ntest'
        expected = '<div ' \
        'class="good_example">\n  <div class="title">\n\t' \
        '<span class="select_code" id="link3">' \
        'SELECT ALL</span>\n\t\n\t<span>CORRECT EXAMPLE:</span>\n</div>' \
        '\n    \n    <div class="code">' \
        '\n        <pre id="codelink3">test\n</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

    def test_macro_with_invalid_lang(self):
        """ Testing the expand_macro method with invalid language. """
        processor = CodeExample(self.env)
        args = '#!python1\ntest'
        formatter = Formatter(self.env, self.context)

        name = 'CodeExample'
        expected = '<div ' \
        'class="example">\n  <div class="title">\n\t' \
        '<span class="select_code" id="link1">' \
        'SELECT ALL</span>\n\t\n\t<span>EXAMPLE:</span>\n</div>\n    \n    ' \
        '<div class="system-message">\n    <strong>' \
        'During the example analyzing the following problems appear:' \
        '</strong>\n    ' \
        '<ul>\n        <li>no lexer for alias \'python1\' found</li>' \
        '\n    </ul>\n    </div>\n    \n    ' \
        '<div class="code">' \
        '\n        <pre id="codelink1">test\n</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

    def test_pygmentize_args(self):
        """ Testing the pygmentize_args method. """
        processor = CodeExample(self.env)
        args = 'test1'
        pygmentized = 'test1\n'
        self.assertEqual(pygmentized, processor.pygmentize_args(args, True))
        self.assertEqual(args, processor.pygmentize_args(args, False))

    def test_pygmentize_with_python(self):
        """ Testing the pygmentize_args method with Python code. """
        processor = CodeExample(self.env)
        args = '#!python\ntest1'
        pygmentized = 'test1\n'
        self.assertEqual(pygmentized, processor.pygmentize_args(args, True))

    def test_invalid_lang(self):
        """ Testing the pygmentize_args method with invalid language. """
        processor = CodeExample(self.env)
        args = '#!python1\ntest1\n'
        pygmentized = 'test1\n\n'
        self.assertEqual(pygmentized, processor.pygmentize_args(args, True))

    def test_pygmentize_multiline(self):
        """ Testing the pygmentize_args method with multiline code. """
        processor = CodeExample(self.env)
        args = '#!python\ndef Class:\n    pass\n'
        pygmentized = '<span class="k">def</span> ' \
        '<span class="nf">Class</span><span class="p">:</span>\n' \
        '    <span class="k">pass</span>\n\n'
        self.assertEqual(pygmentized, processor.pygmentize_args(args, True))

    def test_pygmentize_with_windows_new_lines(self):
        """ Testing the pygmentize_args method with Windows new lines. """
        processor = CodeExample(self.env)
        args = '#!python\r\ndef Class:\n    pass\n'
        pygmentized = '<span class="k">def</span> ' \
        '<span class="nf">Class</span><span class="p">:</span>\n' \
        '    <span class="k">pass</span>\n\n'
        self.assertEqual(pygmentized, processor.pygmentize_args(args, True))

    def test_render_as_lang(self):
        """ Testing the render_as_lang method. """
        processor = CodeExample(self.env)
        lang = 'python'
        content = 'def Class:\n    pass\n'
        pygmentized = '<span class="k">def</span> ' \
        '<span class="nf">Class</span><span class="p">:</span>\n' \
        '    <span class="k">pass</span>\n'
        self.assertEqual(pygmentized, processor.render_as_lang(lang, content))

    def test_csharp_render(self):
        """ Testing the CSharp rendering. """
        processor = CodeExample(self.env)
        content = '#!c#\ndouble test() {}'
        pygmentized = '<span class="kt">double</span> ' \
            '<span class="nf">test</span><span class="p">()</span> ' \
            '<span class="p">{}</span>\n'
        self.assertEqual(pygmentized, processor.pygmentize_args(content, True))

    def test_get_htdocs_dirs(self):
        """ Testing get_htdocs_dirs method. """
        processor = CodeExample(self.env)
        htdocs = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              '..', 'htdocs'))
        self.assertEqual(processor.get_htdocs_dirs(), [('ce', htdocs)])

    def test_path_recognition(self):
        """ Testing correct path requirements. """
        processor = CodeExample(self.env)
        args = '##path=test\nТЕСТ'
        formatter = Formatter(self.env, self.context)

        name = 'CodeExample'
        expected = '<div ' \
        'class="example">\n  <div class="title">\n\t' \
        '<span class="select_code" id="link1">' \
        'SELECT ALL</span>\n\t\n\t<span>EXAMPLE:</span>\n</div>\n    \n    ' \
        '<div class="system-message">\n    <strong>' \
        'During the example analyzing the following problems' \
        ' appear:</strong>\n    <ul>\n        ' \
        '<li>Path element is not found.</li>\n    '\
        '</ul>\n    </div>' \
        '\n    \n    <div class="code">' \
        '\n        <pre id="codelink1">ТЕСТ\n</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

    def test_get_quote(self):
        """ Testing getting quote from the text. """
        processor = CodeExample(self.env)
        text = 'one\ntwo\nthree'
        args = '##regex=two\n##lines=1'
        processor._args = args
        processor.extract_options()
        expected = 'two'
        self.assertEqual(expected, processor.get_quote(text, args))

    def test_get_quote_without_match(self):
        """ Testing getting quote from the text without regex match. """
        processor = CodeExample(self.env)
        text = 'one\ntwo\nthree'
        args = '##regex=four'
        processor._args = args
        processor.extract_options()
        expected = 'two'
        self.assertEqual(text, processor.get_quote(text, args))

    class RepositoryManager:

        def __init__(self, is_incorrect=False):
            self.is_incorrect = is_incorrect

        def get_repository(self, param):
            repo = param

            class Repo:

                def __init__(self, is_incorrect=False):
                    self.is_incorrect = is_incorrect

                def get_node(self, path, rev=None):

                    class Node:

                        path = ''

                        def get_content(self):

                            class Stream:

                                def read(self):
                                    if repo:
                                        return 'repo:' + repo
                                    return 'test'
                            return Stream()
                    if self.is_incorrect:
                        raise NoSuchNode("1", "1")
                    return Node()

            return Repo(self.is_incorrect)

        def shutdown(self):
            pass

    def test_get_sources(self):
        """ Testing getting sources. """
        processor = CodeExample(self.env)
        processor.get_repos_manager = lambda: self.RepositoryManager()
        src = '##path=1'
        processor._args = src
        processor.extract_path()
        expected = 'test'
        self.assertEqual(expected, processor.get_sources(src))

    def test_get_repo(self):
        """ Testing getting sources. """
        processor = CodeExample(self.env)
        processor.get_repos_manager = lambda: self.RepositoryManager()
        src = '##repo=1\n##path=1'
        processor._args = src
        processor.extract_options()
        expected = 'repo:1'
        self.assertEqual(expected, processor.get_sources(src))

    def test_broken_repos(self):
        """ Testing broken repository. """

        def get_broken_repos():
            raise TracError('')

        processor = CodeExample(self.env)
        processor.get_repos_manager = get_broken_repos
        src = ''
        expected = ''
        self.assertEqual(expected, processor.get_sources(src))

    def test_get_sources_with_incorrect_path(self):
        """ Testing getting sources with incorrect path. """
        processor = CodeExample(self.env)
        processor.get_repos_manager = lambda: self.RepositoryManager()
        src = 'path1=1'
        self.assertEqual(src, processor.get_sources(src))

    def test_get_sources_with_missing_file(self):
        """ Testing getting sources with incorrect path. """
        processor = CodeExample(self.env)
        processor.get_repos_manager = lambda: self.RepositoryManager(True)
        src = '##path=1'
        processor._args = src
        processor.extract_path()
        self.assertEqual(src, processor.get_sources(src))

    def test_link_updating_with_index(self):
        """ Testing adding anchor to the source link. """
        processor = CodeExample(self.env)
        processor._link = 'path'
        processor._args = "##regex=def"
        processor.extract_options()
        processor.get_quote("test1\ndef\ntest2", "")
        expected = 'path#L2'
        self.assertEqual(expected, processor._link)

    def test_parse_path(self):
        """ Testing correctness of parsing path. """
        processor = CodeExample(self.env)

        def get_lines(path):
            processor._args = path
            processor.extract_path()
            return processor._path[2]

        def get_focus_line(path):
            processor._args = path
            processor.extract_path()
            return processor._path[3]

        self.assertEqual('100', get_lines('##path=path@rev:100'))
        self.assertEqual('26-30', get_lines('##path=path@rev:26-30'))
        self.assertEqual('26-30,32-34,40',
            get_lines('##path=path@rev:26-30,32-34,40'))
        self.assertEqual(100, get_focus_line('##path=path@rev:100#L100'))

    def test_get_range(self):
        """ Testing getting required range from parsed lines. """
        self.assertEqual([26, 27, 28, 29, 30, 32, 33, 34, 40],
                         CodeExample.get_range('26-30,32-34,40'))

    def test_get_analyzed_content(self):
        """ Testing getting required range from the text."""
        processor = CodeExample(self.env)
        text = 'one\ntwo\nthree\nfour'
        lines = '1-2, 4'
        expected = [(0, 'one'), (1, 'two'), (3, 'four')]
        self.assertEqual(expected, processor.get_analyzed_content(text, lines))

    def test_focus_line(self):
        """ Testing generating URL with focus line. """
        processor = CodeExample(self.env)
        processor._link = 'path'
        processor.get_quote('', '', '', 100)
        self.assertEqual('path#L100', processor._link)


class ImportTestCase(MockerTestCase):

    def test_import(self):
        """ Testing with pygments not installed. """

        import_stub = self.mocker.replace('__builtin__.__import__')
        self.expect(import_stub(mocker.MATCH(lambda x: x.count('pygments')),
                                  mocker.ANY, mocker.ANY, mocker.ANY)).\
                                  count(0, None)

        def import_errror_raiser(name, globals, locals, fromlist):
            raise ImportError

        self.mocker.call(import_errror_raiser)
        self.mocker.replay()
        import codeexample.code_example_processor
        reload(codeexample.code_example_processor)
        from codeexample.code_example_processor import CodeExample
        self.assertEqual(CodeExample.is_have_pygments(), False)


def suite():
    """ Create a testing suite. """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CodeExampleTestCase, 'test'))
    suite.addTest(unittest.makeSuite(ImportTestCase, 'test'))
    return suite
