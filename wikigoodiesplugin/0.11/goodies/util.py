# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Christian Boos <cboos@neuf.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Christian Boos <cboos@neuf.fr>

import re

from genshi.builder import tag
from genshi.core import Markup

from trac.util.presentation import group


def prepare_regexp(d):
    syms = d.keys()
    syms.sort(lambda a, b: cmp(len(b), len(a)))
    return "|".join([r"%s%s%s"
                     % (re.match(r"\w", s[0]) and r"\b" or "",
                        re.escape(s),
                        re.match(r"\w", s[-1]) and r"\b" or "")
                     for s in syms])


def render_table(items, colspec, render_item):
    try:
        columns = max(int(colspec), 1)
    except:
        columns = 3

    nbsp = Markup('&nbsp;')
    hdr = [tag.th('Markup', nbsp), tag.th(nbsp, 'Display')]
    def render_def(s):
        rendered = s and render_item(s) or None
        return [tag.td(s), tag.td(rendered)] 
    
    return tag.table(tag.tr((hdr + [tag.th(nbsp)]) * (columns-1) + hdr),
                     [tag.tr([render_def(s) + [tag.td(nbsp)]
                              for s in row[:-1]] + render_def(row[-1]))
                      for row in group(sorted(items), columns)],
                     class_="wiki")
