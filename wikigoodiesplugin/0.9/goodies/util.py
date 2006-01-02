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

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from trac.util import escape, Markup


def render_table(items, colspec, render_item):
    try:
        columns = max(int(colspec), 1)
    except:
        columns = 3
    buf = StringIO()
    buf.write('<table class="wiki">'
              ' <tr>')
    headers = ['<th>Markup&nbsp;</th><th>&nbsp;Display</th>'] * columns
    buf.write('  <th>&nbsp;</th>'.join(headers))
    buf.write(' </tr>')
    items = items[:]
    items.sort()
    rows = []
    while items:
        rows.append(items[0:columns])
        items[0:columns] = []
    for r in rows:
        buf.write('<tr>')
        buf.write('<td>&nbsp;</td>'.join(['<td>%s</td><td>%s</td>' % \
                                          (escape(s), render_item(s))
                                          for s in r]))
        buf.write('</tr>')
    buf.write('</table>')
    return buf.getvalue()



