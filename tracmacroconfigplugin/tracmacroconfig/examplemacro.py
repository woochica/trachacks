"""An example macro using TracMacroConfig, called [[TracMacroConfigExample]]

The macro does nothing exciting: it just displays the parameters it was
called with.
"""

from genshi.builder import tag
from trac.wiki.macros import WikiMacroBase

from tracmacroconfig import TracMacroConfig

class TracMacroConfigExample(WikiMacroBase):

    mc = TracMacroConfig('macroconfig-example')

    mo_text = mc.Option('text', default='exampletext',
                    doc='''A string macro option''')

    mo_bool = mc.BoolOption('bool', default=True,
                    doc='''A bool macro option''')

    mo_int = mc.IntOption('int', default=42,
                    doc='''An integer macro option''')

    mo_list = mc.ListOption('list', default=['first', 'last'], sep='|',
                    doc='''A list macro option''')

    mo_nodtext = mc.Option('nodtext', default=None,
                    doc='''A string macro option without default''')

    mo_nodbool = mc.BoolOption('nodbool', default=None,
                    doc='''A bool macro option without default''')

    mo_nodint = mc.IntOption('nodint', default=None,
                    doc='''An integer macro option without default''')

    mo_nodlist = mc.ListOption('nodlist', default=None, sep='|',
                    doc='''A list macro option without default''')

    mc.InheritOption('config', doc='''Inherit options from that list''')

    def __init__(self):
        self.mc.setup(self.config)

    def expand_macro(self, formatter, name, arguments):
        self.mc.options(arguments)
        extras = self.mc.extras()
        extra = ''
        if 'extra' in extras:
            extra = extras['extra']
        return tag.div(
            tag.h3('[[%s(%s)]]' % ( name, arguments )),
            tag.table(
              tag.tr(
                tag.th('Name'), tag.th('Value'), tag.th('Qualified'),
                tag.th('Default?'), tag.th('Macroarg?'), tag.th('Extra?'),
                tag.th('Known?'), tag.th('Default'), tag.th('Documentation')
              ),
              self._show_option('text', self.mo_text,
                                TracMacroConfigExample.mo_text),
              self._show_option('bool', self.mo_bool,
                                TracMacroConfigExample.mo_bool),
              self._show_option('int', self.mo_int,
                                TracMacroConfigExample.mo_int),
              self._show_option('list', self.mo_list,
                                TracMacroConfigExample.mo_list),
              self._show_option('nodtext', self.mo_nodtext,
                                TracMacroConfigExample.mo_nodtext),
              self._show_option('nodbool', self.mo_nodbool,
                                TracMacroConfigExample.mo_nodbool),
              self._show_option('nodint', self.mo_nodint,
                                TracMacroConfigExample.mo_nodint),
              self._show_option('nodlist', self.mo_nodlist,
                                TracMacroConfigExample.mo_nodlist),
              self._show_extra('extra', extra),
              border=1, cellpadding=1, cellspacing=0
            )
        )

    def _show_option(self, name, val, spec):
        return tag.tr(
          tag.td('%s' % name),
          tag.td('%s' % val),
          tag.td('%s %s' % self.mc.option_qualified_name(name)),
          tag.td('%s' % self.mc.option_is_default(name)),
          tag.td('%s' % self.mc.option_is_macroarg(name)),
          tag.td('%s' % self.mc.option_is_extra(name)),
          tag.td('%s' % self.mc.option_is_known(name)),
          tag.td('%s' % str(spec.default)),
          tag.td('%s' % spec.__doc__)
        )

    def _show_extra(self, name, val):
        return tag.tr(
          tag.td('%s' % name),
          tag.td('%s' % val),
          tag.td('%s %s' % self.mc.option_qualified_name(name)),
          tag.td('%s' % self.mc.option_is_default(name)),
          tag.td('%s' % self.mc.option_is_macroarg(name)),
          tag.td('%s' % self.mc.option_is_extra(name)),
          tag.td('%s' % self.mc.option_is_known(name)),
          tag.td(''),
          tag.td('')
        )

