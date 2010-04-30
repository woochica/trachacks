# -*- coding: utf-8 -*-

from trac.wiki.formatter import WikiProcessor
from trac.wiki.macros import WikiMacroBase

class MacroChainProcessor(WikiMacroBase):
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
      [[MacroChain(Include(http://www.example.com/), text/html)]]  # Same as MimeInclude macro
      [[MacroChain(Include(http://www.example.com/foo.csv), CsvMacro)]]
      [[MacroChain(Xslt(graph.xslt, doc.xml), graphviz.dot)]]
    }}}
    """

    def get_macros(self):
        yield 'MacroChain'

    def expand_macro(self, formatter, name, content):
        macros, content = self._parse_args(content)
        if len(macros) < 1:
            raise Exception("Insufficient arguments.")

        for name in macros:
            try:
                macro = WikiProcessor(formatter, name)
		if macro.error:
		    raise Exception('Failed to load macro %s: \'%s\'' % (name, macro.error))
                content = str(macro.process(content))
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

