# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2009 Edgewall Software
# Copyright (C) 2013 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import difflib
import re
import unittest

from trac.util.text import to_unicode
from trac.wiki.formatter import HtmlFormatter, InlineHtmlFormatter


class WikiTestCase(unittest.TestCase):

    generate_opts = {}

    def __init__(self, title, input, correct, file, line, setup=None,
                 teardown=None):
        unittest.TestCase.__init__(self, 'test')
        self.title = title
        self.input = input
        self.correct = correct
        self.file = file
        self.line = line
        self._setup = setup
        self._teardown = teardown

    def setUp(self):
        if self._setup:
            self._setup(self)

    def tearDown(self):
        self.env.reset_db()
        if self._teardown:
            self._teardown(self)

    def test(self):
        """Testing WikiFormatter"""
        formatter = self.formatter()
        v = unicode(formatter.generate(**self.generate_opts))
        v = v.replace('\r', '').replace(u'\u200b', '')
        try:
            self.assertEquals(self.correct, v)
        except AssertionError, e:
            msg = to_unicode(e)
            match = re.match(r"u?'(.*)' != u?'(.*)'", msg)
            if match:
                g1 = ["%s\n" % x for x in match.group(1).split(r'\n')]
                g2 = ["%s\n" % x for x in match.group(2).split(r'\n')]
                expected = ''.join(g1)
                actual = ''.join(g2)
                wiki = repr(self.input).replace(r'\n', '\n')
                diff = ''.join(list(difflib.unified_diff(g1, g2, 'expected',
                                                         'actual')))
                # Tip: sometimes, 'expected' and 'actual' differ only by 
                #      whitespace, so it can be useful to visualize them, e.g.
                # expected = expected.replace(' ', '.')
                # actual = actual.replace(' ', '.')
                def info(*args):
                    return '\n========== %s: ==========\n%s' % args
                msg = info('expected', expected)
                msg += info('actual', actual)
                msg += info('wiki', ''.join(wiki))
                msg += info('diff', diff)
            raise AssertionError( # See below for details
                '%s\n\n%s:%s: "%s" (%s flavor)' \
                % (msg, self.file, self.line, self.title, formatter.flavor))

    def formatter(self):
        return HtmlFormatter(self.env, self.context, self.input)

    def shortDescription(self):
        return 'Test ' + self.title


class OneLinerTestCase(WikiTestCase):
    def formatter(self):
        return InlineHtmlFormatter(self.env, self.context, self.input)

class EscapeNewLinesTestCase(WikiTestCase):
    generate_opts = {'escape_newlines': True}
    def formatter(self):
        return HtmlFormatter(self.env, self.context, self.input)


def suite(data=None, setup=None, file=__file__, teardown=None, context=None):
    suite = unittest.TestSuite()
    def add_test_cases(data, filename):
        tests = re.compile('^(%s.*)$' % ('=' * 30), re.MULTILINE).split(data)
        next_line = 1
        line = 0
        for title, test in zip(tests[1::2], tests[2::2]):
            title = title.lstrip('=').strip()            
            if line != next_line:
                line = next_line
            if not test or test == '\n':
                continue
            next_line += len(test.split('\n')) - 1
            if 'SKIP' in title or 'WONTFIX' in title:
                continue
            blocks = test.split('-' * 30 + '\n')
            page_escape_nl = oneliner = None
            if len(blocks) < 4:
                blocks.extend([None,] * (4 - len(blocks)))
            input, page, oneliner, page_escape_nl = blocks[:4]
            if page:
                page = WikiTestCase(
                    title, input, page, filename, line, setup,
                    teardown)
            if oneliner:
                oneliner = OneLinerTestCase(
                    title, input, oneliner[:-1], filename, line, setup,
                    teardown, context)
            if page_escape_nl:
                page_escape_nl = EscapeNewLinesTestCase(
                    title, input, page_escape_nl, filename, line, setup,
                    teardown, context)
            for tc in [page, oneliner, page_escape_nl]:
                if tc:
                    suite.addTest(tc)
    if data:
        add_test_cases(data, file)
    return suite
