""" @package IniGetMacro
    @file macro.py
    @brief The IniGetMacro class

    Return the value of a trac.ini [section] option as plain text.

    @author Douglas Clifton <dwclifton@gmail.com>
    @date December, 2008
    @version 0.11.3
"""

from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import system_message
from trac.config import Option
import re

__all__ = ['IniGetMacro']

class IniGetMacro(WikiMacroBase):
    """The macro call `[[IniGet(section.name)]]` returns the value of the
    `trac.ini` option `name` in `section`.
    
    Example: `[[IniGet(project.name)]]` yields "[[IniGet(project.name)]]"
    
    '''Note:''' allowing users to see values in `trac.ini` can be considered a
    security risk.
    """

    def expand_macro(self, formatter, name, args):
        """Return value of a trac.ini [section].option as plain text."""
        
        if args.find('.') == -1:
            return system_message('%s: Invalid parameter: "%s"' % (name, args))
        section, option = re.sub('\s+', '', args).split('.', 1)

        if self.config.has_option(section, option):
            return (self.config.get(section, option))
        else:
            return system_message('%s: No option "%s" in section [%s]' % (name,
                                                                          option,
                                                                          section))
