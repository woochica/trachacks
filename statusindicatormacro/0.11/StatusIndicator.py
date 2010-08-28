#
# StatusIndicatorMacro for Trac
# Version: 5.5
#
# Author: iceboy <iceboy@iceboy.de>
# License: GPL 3.0
#
from StringIO import StringIO
from trac.wiki.macros import WikiMacroBase
import string
from trac.core import *
from trac.wiki.formatter import format_to_html

revision = "$Rev$"
url = "$URL$"

class StatusIndicatorMacro(WikiMacroBase):
    """Inserts a square dot in the give color, white if no color given"""

    def expand_macro(self, formatter, name, args):
	if args:
		color = args
	else:
		color = "white"	
	buf = StringIO()
        buf.write('<div style="display:inline;color:%s;">&#x2587;</div>' % color)

        return buf.getvalue()
