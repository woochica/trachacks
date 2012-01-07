#!/bin/env python
# -*- coding: utf-8 -*-

# ShowWhen Macro; version 0.1
# Copyright (C) 2012 MATOBA Akihiro (a.k.a. matobaa)
# <matobaa+trac-hacks@gmail.com>
   
""" Licensed under the MIT License.
See: http://trac-hacks.org/wiki/ShowWhenMacro
"""

from datetime import datetime
from genshi.builder import tag, Markup
from trac.core import Component, implements
from trac.util.datefmt import parse_date, utc
from trac.wiki import IWikiMacroProvider
from trac.wiki.formatter import format_to_html
import re

class ShowWhen(Component):
    """ Shows content in spacified time range. """
    implements(IWikiMacroProvider)
    
    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'ShowWhen'

    def get_macro_description(self, name):
        return """Shows content in spacified time range. (In Japanese/KANJI) 指定した時間帯にコンテンツを表示します。[[BR]]
コンテンツはWikiフォーマットされます。
time from, time to, and content can specify in wiki-table style as follows:
{{{
    {{{
    #!ShowWhen
    || 2012-01-04T00:00:00 || 2012-01-04T23:59:59 || [[Image(wiki:SandBox:yutori01.gif)]] Wednesday is Refresh-day. go home early!
    || 2012-01-11T00:00:00 || 2012-01-11T23:59:59 || [[Image(wiki:SandBox:yutori01.gif)]] 水曜日はリフレッシュデーです。早く帰ろう!
    || 2012-01-18T00:00:00 || 2012-01-18T23:59:59 || [[Image(wiki:SandBox:yutori01.gif)]] 水曜日はリフレッシュデーです。メリハリをつけよう!
    || 2012-01-20T00:00:00 || 2012-01-20T23:59:59 || [[Image(wiki:SandBox:yutori01.gif)]] 給料日はリフレッシュデーです。帰って家族の顔を見よう!
    }}}
}}}
Scan from top, a first matched line will be shown.[[BR]]
上から走査し、条件を満たす最初の行が表示されます。
"""

    def expand_macro(self, formatter, name, content, args=None):
        hint = '|| yyyy-mm-ddThh:mm:ss || yyyy-mm-ddThh:mm:ss || message'
        pattern = "\s*||(.*)||(.*)||(.*)".replace('|','\|')
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
                    by, to = parse_date(by,None,hint), parse_date(to,None,hint)
                    self.env.log.debug('parsed time range: %s / %s' % (by,to))
                    if by <= now and now <= to:
                        return format_to_html(self.env, formatter.context, text)
            return None
        except Exception,e:
            return tag.div(tag.strong(e.title), ': ' + e.message, class_="system-message")
