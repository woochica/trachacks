## -*- coding: utf-8 -*-
##
##  Copyright (c) 2008 Ashish Kulkarni <kulkarni.ashish@gmail.com>
##
##  This software is provided 'as-is', without any express or implied
##  warranty.  In no event will the authors be held liable for any damages
##  arising from the use of this software.
##
##  Permission is granted to anyone to use this software for any purpose,
##  including commercial applications, and to alter it and redistribute it
##  freely, subject to the following restrictions:
##
##  1. The origin of this software must not be misrepresented; you must not
##     claim that you wrote the original software. If you use this software
##     in a product, an acknowledgment in the product documentation would be
##     appreciated but is not required.
##  2. Altered source versions must be plainly marked as such, and must not be
##     misrepresented as being the original software.
##  3. This notice may not be removed or altered from any source distribution.

from trac.util.html import Markup
from trac.wiki import format_to_oneliner
from trac.wiki.macros import WikiMacroBase
from genshi.builder import tag

import re, StringIO, inspect

revison = "$Rev$"
url     = "$URL$"

KEY_REGEX    = re.compile('^([^\s]+.*)\:\s*$', re.I)
ATTRIB_REGEX = re.compile('^(\s+)@([^@\s]+?)\:\s*(.+)?$', re.I)

class FlatTableProcessor(WikiMacroBase):
    """WikiProcessor for displaying a table with the markup being entered in a flat form."""

    CONFIG_KEY = 'flat-table'
    DESC_KEY   = '.description'

    def __init__(self):
        self.CONFIG = {}
        self.DESC   = {}
        conf = self.env.config
        for key, ignored in conf.options(self.CONFIG_KEY):
            if key.endswith(self.DESC_KEY):
                continue
            cols = conf.getlist(self.CONFIG_KEY, key)
            self.CONFIG[key] = self._parse_config(cols)
            self.DESC  [key] = conf.get(self.CONFIG_KEY, key+self.DESC_KEY)

    def _parse_config(self, cols):
        config = []
        for col in cols:
            name, val = col.split(':', 1)
            config.append( (name.strip(), [item.strip() for item in val.split()]) )
        return config

    def get_macros(self):
        yield self.CONFIG_KEY
        for key in self.CONFIG.keys():
            yield key

    def get_macro_description(self, name):
        if name == self.CONFIG_KEY:
            return inspect.getdoc(self.__class__)

        doc = self.DESC[name] + '\n'
        doc += " || '''Column Name''' || '''Aliases''' || \n"
        for desc, keys in self.CONFIG[name]:
            doc += ' || ' + desc + ' || ' + ', '.join(keys) + ' || \n'
        return doc

    def expand_macro(self, formatter, name, args):
        if not args:
            return Markup()

        config = None
        if name == self.CONFIG_KEY:
            lines = args.splitlines()
            if not lines or not lines[0].startswith('#!'):
                return Markup()
            config = self._parse_config([i.strip() for i in lines[0][2:].split(',')])
        else:
            config = self.CONFIG[name]

        if not config:
            return Markup()

        def to_html(text):
            if not text:
                return ''
            return Markup('<br>'.join([format_to_oneliner(self.env, formatter.context, line) \
                                for line in text.splitlines()]))

        def has_keys(dict, keys):
            for key in keys:
                if dict.has_key(key):
                    return True
            return False

        rows = self.parse_doc(args)
        if not rows:
            return Markup()

        seen = []
        for desc, keys in config:
            if [row for row in rows if has_keys(row, keys)]:
                seen.append(desc)

        thead = tag.thead()
        for desc, keys in config:
            if not desc in seen:
                continue
            thead(tag.td(tag.b(desc)))

        tbody = tag.tbody()
        for row in rows:
            trow = tag.tr()
            for desc, keys in config:
                if not desc in seen:
                    continue
                tcol = tag.td()
                for key in keys:
                    if row.has_key(key):
                        tcol(to_html(row[key]))
                trow(tcol)
            tbody(trow)

        return tag.table([thead, tbody], class_='wiki')

    def parse_doc(self, text):
        columns = []
        column  = {}
        attr, val, spaces = '', '', ''
        for line in text.splitlines():
            if not line.strip() or line.startswith('#'):
                continue

            match = KEY_REGEX.match(line)
            if match:
                if column:
                    if attr and val:
                        column[attr] = val.strip()
                    columns.append(column)
                column, attr, val, spaces = {}, '', '', ''
                column['key'] = match.group(1)
                continue

            match = ATTRIB_REGEX.match(line)
            if match:
                if val:
                    column[attr] = val.strip()
                spaces = match.group(1)
                attr   = unicode(match.group(2))
                val    = match.group(3) or ''
                continue

            if line.startswith(spaces):
                val += line.strip() + '\n'

        if column:
            if attr and val:
                column[attr] = val.strip()
            columns.append(column)
        return columns
