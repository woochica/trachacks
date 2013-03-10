#!/bin/env python
# -*- coding: utf-8 -*-

# ShowWhen Macro; version 0.1
# Copyright (C) 2012 MATOBA Akihiro (a.k.a. matobaa)
# <matobaa+trac-hacks@gmail.com>

""" Licensed under the MIT License.
See: http://trac-hacks.org/wiki/ShowWhenMacro
"""

# Permission is hereby granted, free of charge, to any person  obtaining  a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the  rights  to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit  persons  to  whom  the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall  be  included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES  OF  MERCHANTABILITY,
# FITNESS  FOR  A  PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY,  WHETHER  IN  AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH  THE  SOFTWARE  OR  THE  USE  OR  OTHER
# DEALINGS IN THE SOFTWARE.

from datetime import datetime
from genshi.builder import tag
from trac.core import Component, implements
from trac.util.datefmt import parse_date, utc
from trac.wiki import IWikiMacroProvider
from trac.wiki.formatter import format_to_html
import re


class ShowWhen(Component):
    """ Shows content in specified time range. """
    implements(IWikiMacroProvider)

    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'ShowWhen'

    def get_macro_description(self, name):
        return """Shows content in specified time range.
time from, time to, and content will be specified like [wiki:WikiFormatting#SimpleTables wiki-table style] as follows:
{{{
    {{{
    #!ShowWhen
    || 2012-01-04                || 2012-01-04T23:59:59       || [[Image(wiki:SandBox:yutori01.gif)]] Wednesday is Refresh-day. go home early!
    || 2012-07-13T00:00:00+09:00 || 2012-07-13T23:59:59+09:00 || [[Image(wiki:SandBox:birthday.gif)]] Happy Birthday, matobaa!
    || 2012-11-13T22:10:54Z      || 2012-11-13T22:14:56Z      || Look at the Moon! Total Eclipse!
     }}}
}}}
Scan from top, a first matched line will be shown.[[BR]]
datetime string should be specified as RFC:3339 5.6 Internet date/time format. If no timezone is specified, use server-default.[[BR]]
[[BR]] (In Japanese/KANJI) [wiki:WikiFormatting#SimpleTables 表形式]で指定した時間帯にコンテンツを表示します。コンテンツはWikiフォーマットされます。
表は上から走査され、条件を満たす最初の行が表示されます。[[BR]]
日付書式は RFC:3339 の 5.6 Internet date/time Format で指定します。タイムゾーンを指定しない場合、サーバのデフォルトタイムゾーンを用います。
"""

    def expand_macro(self, formatter, name, content, args=None):
        hint = '|| yyyy-mm-ddThh:mm:ss || yyyy-mm-ddThh:mm:ss || message'
        pattern = "\s*||(.*)||(.*)||(.*)".replace('|', '\|')
        pattern = re.compile(pattern)
        try:
            if content == None:
                return tag.div('ShowWhen Macro is not supported. Use WikiProcessor-style instead.', \
                               class_="system-message")
            now = datetime.now(utc)
            for line in content.split('\n'):
                matched = pattern.match(line)
                if matched:
                    result = matched.groups()
                    by, to, text = result
                    by, to = parse_date(by, None, hint), parse_date(to, None, hint)
                    self.env.log.debug('parsed time range: %s / %s' % (by, to))
                    if by <= now and now <= to:
                        return format_to_html(self.env, formatter.context, text)
            return None
        except Exception, e:
            return tag.div(tag.strong(e.title), ': ' + e.message, class_="system-message")
