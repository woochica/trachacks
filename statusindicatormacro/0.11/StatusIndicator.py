#
# BackLinks plugin for Trac
# Version: 5.5
#
# Author: Trapanator trap@trapanator.com
# Website: http://www.trapanator.com/blog/archives/category/trac
# License: GPL 3.0
#
from StringIO import StringIO
from genshi.builder import tag
from trac.wiki.macros import WikiMacroBase
import string
from trac.core import *
from trac.wiki.formatter import format_to_html
from trac.util import TracError
from trac.util.text import to_unicode
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule

class StatusIndicatorMacro(WikiMacroBase):
    """Inserts a square dot in the give color, white if no color given"""

    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, args):
	if args:
		color = args
	else:
		color = "white"	
	buf = StringIO()
        buf.write('<div style="display:inline;color:%s;">&#x2587;</div>' % color)

        return buf.getvalue()
