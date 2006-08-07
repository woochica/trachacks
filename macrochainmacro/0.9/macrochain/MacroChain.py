# -*- coding: utf-8 -*-
"""
Chain together multiple macros.

This macro allows you to chain together multiple macros; that is, feed the
output from one macro to the input of the next. Usually the second and
subsequent macros will be WikiProcessors, but this is not a requirement (if
they aren't then the output from the previous macro will be treated as the
arguments to the next macro).

Arguments: a comma-separated list of macro names; the first macro may also have
a list of arguments enclosed in parentheses. Any known macro may be specified,
including all the wiki processors.

Examples:
{{{
  [[MacroChain(macro1, macro2, macro3, macro4)]]
  [[MacroChain(Include(http://www.example.com/, None), text/html)]]  # Same as MimeInclude macro
  [[MacroChain(Include(http://www.example.com/foo.csv, None), CsvMacro)]]
  [[MacroChain(Xslt(graph.xslt, doc.xml), graphviz.dot)]]
}}}
"""

import inspect
import sys

from trac.core import Component, implements
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import WikiProcessor

class MacroChainProcessor(Component):
    implements(IWikiMacroProvider)

    # IWikiMacroProvider interface

    def get_macros(self):
        yield 'MacroChain'

    def get_macro_description(self, name):
        #return inspect.getdoc(inspect.getmodule(self))	# works only in py >= 2.4
        return inspect.getdoc(sys.modules.get(self.__module__))

    def render_macro(self, req, name, content):
        macros, content = self._parse_args(content)
        if len(macros) < 1:
            raise Exception("Insufficient arguments.")

        for name in macros:
            try:
                macro = WikiProcessor(self.env, name)
		if macro.error:
		    raise Exception('Failed to load macro %s: \'%s\'' % (name, macro.error))
                content = macro.process(req, content)
                self.env.log.debug('Macro %s returned \'%s\'' % (name, content))
            except Exception, e:
                self.env.log.error('Macro %s(%s) failed' % (name, content), exc_info=True)
		raise e

        return content

    def _parse_args(self, args):
        firstArgs = None;
        if args.rfind(")"):
            firstArgs = args[args.find("(") + 1 : args.rfind(")")];
            args      = args[:args.find("(")] + args[args.rfind(")") + 1:]

        macros = map(lambda s: s.strip(), args.split(','));

        return macros, firstArgs

