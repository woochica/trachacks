# -*- coding: utf-8 -*-
"""Adds a wiki macro {{{[[MilestoneCompact]]}}} which lists and describes the
project's milestones in a compact form.
"""

import inspect
import sys
from datetime import date
import time

from trac.core import Component, implements
from trac.wiki.api import IWikiMacroProvider
from trac.wiki import format_to_html

revison = "$Rev$"
url = "$URL$"


class MilestoneCompactProcessor(Component):
    implements(IWikiMacroProvider)

    # IWikiMacroProvider interface

    def get_macros(self):
        yield 'MilestoneCompact'

    def get_macro_description(self, name):
        return inspect.getdoc(sys.modules.get(self.__module__))

    def expand_macro(self, formatter, name, arg_content):

        cursor = self.env.get_db_cnx().cursor()

    query = "SELECT name, due, completed, description from milestone order by due;"
    cursor.execute(query)

        miles = [mile for mile in cursor]

        content = []

        init = time.time()
        last = init

        tblMode = False
        if arg_content:
            tblMode = True
            content.append('|| Milestone || Due || Days from now || Days from Previous || Completed || Description ||')

        for name, due, completed, descrip in miles:

            d = date.fromtimestamp(due)
            dd = d.strftime('%b %d, %Y')
            dc = ''
            if completed:
                d = date.fromtimestamp(completed)
                dc = d.strftime('%b %d, %Y')
            dl = int((due - init) / 86400)
            dp = int((due - last) / 86400)

            if not tblMode:
                dt = " '''%s'''" % name
                dt += " ''due %s [in %d days, for %d days]" % (dd, dl, dp)
                if completed:
                    dt += '; completed %s' % dc
                dt += "''::"

                content.append(dt)
                if descrip != None and descrip.strip() != '':
                    content.append('   %s' % descrip)
            else:
                dt = '||%s||%s||%d||%d||%s||%s||' % (name, dd, dl, dp, dc, descrip)
                content.append(dt)

            last = due

        content = '\n'.join(content)

        content = format_to_html(self.env, formatter.context, content)

        content = '<div class="milestone-list">%s</div>' % content

        # to avoid things like the above it might be nicer to use
        # Genshi tag() construction.

        return content
