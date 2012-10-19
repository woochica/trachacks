# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Brian Lynch <blynch1@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import urllib2
from genshi.builder import tag
from trac.wiki.macros import WikiMacroBase

revison = "$Rev$"
url = "http://trac-hacks.org/wiki/DailyLolMacro"
license = "3-Clause BSD"

class DailyLolMacro(WikiMacroBase):
    """Display a picture of a cat with a funny caption.
    Usage:
    {{{
    [[DailyLol]]
    }}}
    """

    def expand_macro(self, formatter, name, content):        

        website = urllib2.urlopen("http://icanhascheezburger.com/")
        website_html = website.read()

        beg_pos = -1
        beg_pos = website_html.find('<img src="', beg_pos + 1)
        end_pos = website_html.find('"', beg_pos + 10)
        raw_url = website_html[beg_pos + 10:end_pos]

        attr = {}
        out = tag.img(src=raw_url, **attr)

        return out
