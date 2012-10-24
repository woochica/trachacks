# -*- coding: utf-8 -*-
#
# Niko Niko Calendar for Trac 0.10
#
# Author: yattom (やっとむ) <yach@alles.or.jp>
# License: BSD
# Modified by: 

import re
import datetime
from StringIO import StringIO

from trac.core import Component, implements
from trac.web.chrome import ITemplateProvider
from trac.wiki.macros import WikiMacroBase

class NikoCaleMacro(WikiMacroBase):
    """Niko-niko Calendar macro.

    {{{
    #!NikoCale
    # you can add comment
    yattom,7/2,(^o^),Had fun at Python Workshop
    morita,7/2,(-_-)
    yattom,7/3,(>_<)
    # empty face can be used for empty cell (like weekends)
    ,2007/7/5,
    }}}

    """
    implements(ITemplateProvider)

    def expand_macro(self, formatter, name, content):
        nikocale = NikoCale(formatter.req)
        for line in content.split('\n'):
            line = line.strip()
            if re.match('^\s*#', line) or re.match('^\s*$', line):
                continue
            parts = line.split(',', 3)
            if not (len(parts) == 3 or len(parts) == 4):
                continue
            if len(parts) == 3:
                parts.append('')
            name, date, niko, comment = parts
            nikocale.add(name.strip(), date.strip(), niko.strip(), comment.strip())

        buf = StringIO()
        txt = nikocale.render(buf)
        return buf.getvalue()

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('nikocale', resource_filename(__name__, 'htdocs'))]


class NikoCale(object):
    GOOD_KEYS = ['(^o^)', 'good', '1']
    ORDINARY_KEYS = ['(-_-)', 'ordinary', 'normal', '2']
    BAD_KEYS = ['(>_<)', 'bad', '3']
    EMPTY_KEYS = ['', '0']
    EMPTY = '&nbsp;'

    def __init__(self, req):
        self.entries = {}
        self.req = req
        self.good = '<IMG src="%s/nikocale/good.png" alt="good!" title="%%(comment)s" />' % req.href.chrome()
        self.ordinary = '<IMG src="%s/nikocale/ordinary.png" alt="ordinary" title="%%(comment)s" />' % req.href.chrome()
        self.bad = '<IMG src="%s/nikocale/bad.png" alt="bad" title="%%(comment)s" />' % req.href.chrome()
        pass

    def add(self, name, date_str, niko_str, comment=''):
        if re.match('^\d+/\d+$', date_str):
            mon, day = date_str.split('/')
            today = datetime.date.today()
            date = datetime.date(today.year, int(mon), int(day))
            if date > today:
                date = datetime.date(date.year - 1, date.month, date.day)
        elif re.match('^\d+/\d+/\d+$', date_str):
            year, mon, day = date_str.split('/')
            date = datetime.date(int(year), int(mon), int(day))
        else:
            raise ValueError('wrong date')

        niko_str = niko_str.strip()
        if niko_str in NikoCale.GOOD_KEYS:
            niko = self.good
        elif niko_str in NikoCale.ORDINARY_KEYS:
            niko = self.ordinary
        elif niko_str in NikoCale.BAD_KEYS:
            niko = self.bad
        elif niko_str in NikoCale.EMPTY_KEYS:
            niko = NikoCale.EMPTY
        else:
            raise ValueError('wrong face: %s'%(niko_str))
        niko = niko%{'comment':comment}

        if not name in self.entries:
            self.entries[name] = {}
        self.entries[name][date] = (niko, comment)

    def render(self, buf):
        names = self.entries.keys()
        if '' in names: names.remove('')
        dates = []
        for e in self.entries.values():
            for d in e:
                if not d in dates:
                    dates.append(d)
        dates.sort()

        buf.write("<table style='border: 1px solid; border-collapse: collapse;'>\n")
        buf.write("  <tr>\n")
        buf.write("    <td style='border: 1px solid'></td>\n")
        for d in dates:
            buf.write("    <td style='border: 1px solid'>%d/%d</td>\n"%(d.month, d.day))
        buf.write("  </tr>\n")

        for n in names:
            buf.write("  <tr>\n")
            buf.write("    <td style='border: 1px solid'>%s</td>\n"%(n))
            for d in dates:
                entry = self.entries[n].get(d)
                if not entry: entry = ('','')
                buf.write("    <td style='border: 1px solid'>%s</td>\n"%(entry[0]))
            buf.write("  </tr>\n")
        buf.write("</table>\n")

        return buf

