# -*- coding: utf-8 -*-
""" Test cases for code example processor. """

import unittest
import os.path
from trac.test import EnvironmentStub, Mock
from trac.web.href import Href
from trac.mimeview.api import Context
from trac.wiki.formatter import Formatter
from codeexample import CodeExample
import imp


class CodeExampleTestCase(unittest.TestCase):
    """ Class with test cases for code example processor. """

    def setUp(self):
        """ Set up the testing environment. """
        self.env = EnvironmentStub(enable=[CodeExample])
        self.req = Mock(base_path = '', chrome = {}, args = {},
                        abs_href = Href('/'), href = Href('/'),
                        session = {}, perm = [], authname = None,
                        tz = None, locale = 'utf-8')
        self.context = Context.from_request(self.req)

    def test_get_macros(self):
        """ Testing the get_macros method. """
        processor = CodeExample(self.env)
        expected_result = ['BadCodeExample', 'CodeExample', 'GoodCodeExample']
        index = 0
        for macros in processor.get_macros():
            self.assertEqual(macros, expected_result[index])
            index += 1

    def test_expand_macro_with_unicode(self):
        """ Testing the expand_macro method with unicode symbols. """
        processor = CodeExample(self.env)
        args = 'ТЕСТ'
        formatter = Formatter(self.env, self.context)

        name = 'CodeExample'
        expected = '<div ' \
        'class="example">\n    <div class="title">EXAMPLE:\n    ' \
        '<span class="select_code" id="link1">' \
        'SELECT ALL</span></div>\n    \n    ' \
        '<div class="code">' \
        '\n        <pre id="codelink1">ТЕСТ</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

    def test_expand_macro(self):
        """ Testing the expand_macro method. """
        processor = CodeExample(self.env)
        args = 'test'
        formatter = Formatter(self.env, self.context)

        name = 'CodeExample'
        expected = '<div ' \
        'class="example">\n    <div class="title">EXAMPLE:\n    ' \
        '<span class="select_code" id="link1">' \
        'SELECT ALL</span></div>\n    \n    ' \
        '<div class="code">' \
        '\n        <pre id="codelink1">test</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

        name = 'BadCodeExample'
        expected = '<div ' \
        'class="bad_example">\n    <div class="title">' \
        'INCORRECT EXAMPLE:\n    ' \
        '<span class="select_code" id="link2">' \
        'SELECT ALL</span></div>\n    \n    ' \
        '<div class="code">' \
        '\n        <pre id="codelink2">test</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

        name = 'GoodCodeExample'
        expected = '<div ' \
        'class="good_example">\n    <div class="title">' \
        'CORRECT EXAMPLE:\n    ' \
        '<span class="select_code" id="link3">' \
        'SELECT ALL</span></div>\n    \n    ' \
        '<div class="code">' \
        '\n        <pre id="codelink3">test</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

    def test_macro_with_invalid_lang(self):
        """ Testing the expand_macro method with invalid language. """
        processor = CodeExample(self.env)
        args = '#!python1\ntest'
        formatter = Formatter(self.env, self.context)

        name = 'CodeExample'
        expected = '<div ' \
        'class="example">\n    <div class="title">EXAMPLE:\n    ' \
        '<span class="select_code" id="link1">' \
        'SELECT ALL</span></div>\n    \n    ' \
        '<div class="system-message">\n    <strong>' \
        'During the example analyzing the following problems appear:' \
        '</strong>\n    ' \
        '<ul>\n        <li>no lexer for alias \'python1\' found</li>' \
        '\n    </ul>\n    </div>\n    \n    ' \
        '<div class="code">' \
        '\n        <pre id="codelink1">test</pre>\n    </div>\n</div>'
        self.assertEqual(expected,
                        processor.expand_macro(formatter, name, args))

    def test_pygmentize_args(self):
        """ Testing the pygmentize_args method. """
        processor = CodeExample(self.env)
        args = 'test1'
        pygmentized = 'test1'
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
        pygmentized = 'test1\n'
        self.assertEqual(pygmentized, processor.pygmentize_args(args, True))

    def test_pygmentize_multiline(self):
        """ Testing the pygmentize_args method with multiline code. """
        processor = CodeExample(self.env)
        args = '#!python\ndef Class:\n    pass\n'
        pygmentized = '<span class="k">def</span> ' \
        '<span class="nf">Class</span><span class="p">:</span>\n' \
        '    <span class="k">pass</span>\n'
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

    def test_render_with_invalid_lang(self):
        """ Testing the render_as_lang method with invalid language. """
        processor = CodeExample(self.env)
        lang = 'python1'
        content = 'def Class:\n    pass\n'
        pygmentized = 'def Class:\n    pass\n'
        self.assertEqual(pygmentized, processor.render_as_lang(lang, content))

    def test_get_htdocs_dirs(self):
        """ Testing get_htdocs_dirs method. """
        processor = CodeExample(self.env)
        htdocs = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              '..', 'htdocs'))
        self.assertEqual(processor.get_htdocs_dirs(), [('ce', htdocs)])


from mocker import MockerTestCase


class ImportTestCase(MockerTestCase):

    def test_import(self):
        """ Testing with pygments not installed. """
        import mocker

        import_stub = self.mocker.replace('__builtin__.__import__')
        self.expect(import_stub(mocker.MATCH(lambda x: x.count('pygments')),
                                  mocker.ANY, mocker.ANY, mocker.ANY)).\
                                  count(0, None)

        def import_errror_raiser(name, globals, locals, fromlist):
            raise ImportError

        self.mocker.call(import_errror_raiser)
        self.mocker.replay()
        import codeexample.code_example_processor
        imp.reload(codeexample.code_example_processor)
        from codeexample.code_example_processor import CodeExample
        self.assertEqual(CodeExample.is_have_pygments(), False)


def suite():
    """ Create a testing suite. """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CodeExampleTestCase, 'test'))
    suite.addTest(unittest.makeSuite(ImportTestCase, 'test'))
    return suite
