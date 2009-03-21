"""
SumMacro: WikiMacro for summing a list of numbers
for Trac: http://trac.edgewall.org
"""

from StringIO import StringIO

from trac.core import *
from trac.wiki.api import IWikiMacroProvider

class SumMacro(Component):
    """WikiMacro for summing a list of numbers"""

    implements(IWikiMacroProvider)

    ### methods for IWikiMacroProvider

    """Extension point interface for components that provide Wiki macros."""

    def expand_macro(self, formatter, name, content):
        """Called by the formatter when rendering the parsed wiki text.

        (since 0.11)
        """

        content = content.strip()
        lines = [i.strip() for i in content.split('\n')]

        _sum = 0.
        precision = 0
        defs = []
        nums = []
        for line in lines:
                parts = line.rsplit(None, 1)
                if len(parts) == 1:
                        defs.append(parts[0])
                        nums.append(None)
                        continue
                try:
                        val = float(parts[1])
                except ValueError:
                        defs.append(line)
                        nums.append(None)
                        continue
                defs.append(parts[0])
                nums.append(val)
                if '.' in parts[1]:
                        preciscion = max((precision, len(parts[1].rsplit('.', 1)[-1])))

        def_len = max([len(i) for i in defs])
        num_len = max([len('%.*f' % (precision, i)) for i in nums if i is not None])
        line_len = def_len + num_len + 2
        buffer = StringIO()
        for num, _def in zip(nums, defs):
                if num is None:
                        print >> buffer, _def
                else:
                        num_str = '%.*f' % (precision, num)
                        print >> buffer, '%s%s%s' % ( _def, ' ' * (line_len - len(_def) - len(num_str)), num_str)

        print >> buffer, '-' * line_len
        _sum = '%.*f' % (precision, sum([i for i in nums if i]))
        print >> buffer, '%s%s' % (' ' * (line_len - len(_sum)), _sum)

        return '<pre class="wiki">%s</pre>' % buffer.getvalue()

    def get_macro_description(self, name):
        """Return a plain text description of the macro with the specified name.
        """
        if name == 'sum':
           return self.__doc__

    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        yield 'sum'

    def render_macro(self, req, name, content):
        """Return the HTML output of the macro (deprecated)"""

        return '<deprecated>'
