# -*- coding: utf-8 -*-
"""Adds a wiki macro [[Components]] which lists and describes the project's components, and links to wiki pages describing the components in more detail, and any tickets for the components.

terry_n_brown@yahoo.com
"""

import inspect
import sys

from StringIO import StringIO
from trac.core import Component, implements
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import Formatter

class ComponentsProcessor(Component):
    implements(IWikiMacroProvider)

    # IWikiMacroProvider interface

    def get_macros(self):
        yield 'Components'

    def get_macro_description(self, name):
        #return inspect.getdoc(inspect.getmodule(self))	# works only in py >= 2.4
        return inspect.getdoc(sys.modules.get(self.__module__))

    def expand_macro(self, formatter, name, content):
        content = []
        cursor = self.env.get_db_cnx().cursor()

	query = "SELECT name, description from component;"
	cursor.execute(query)

        comps = [comp for comp in cursor]
	comps.sort(cmp=lambda x,y: cmp(x[0], y[0]))

        # get a list of all components for which there are tickets
        query = "SELECT distinct component from ticket;"
        cursor.execute(query)
        tickets = [page[0] for page in cursor]

        for name, descrip in comps:
            dt = ' [wiki:%s]' % name
            if name in tickets:
                dt += ' ([query:component=%s tickets])' % name
            dt += '::'
            content.append(dt)
            if descrip != None and descrip.strip() != '':
                content.append('   %s' % descrip)

        content = '\n'.join(content)

        out = StringIO()
        Formatter(self.env, formatter.context).format(content, out)
	return out.getvalue()

    def _parse_args(self, args):
        firstArgs = None;
        if args.rfind(")"):
            firstArgs = args[args.find("(") + 1 : args.rfind(")")];
            args      = args[:args.find("(")] + args[args.rfind(")") + 1:]

        macros = map(lambda s: s.strip(), args.split(','));

        return macros, firstArgs
