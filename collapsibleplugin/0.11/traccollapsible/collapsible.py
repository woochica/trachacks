#   Copyright 2010 Matthew Noyes <thecodingking at gmail.com>   
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

__author__ = 'Matthew Noyes'

from genshi.builder import tag

from trac.core import *
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from StringIO import StringIO
from trac.wiki.formatter import format_to_html
from trac.util import TracError
from trac.util.text import to_unicode
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule

__all__ = ['CollapsiblePlugin']


class CollapsibleStartMacro(WikiMacroBase):
    r"""CollapsibleStartMacro marks the start of a collapsible list

    Example:    
    `[[CollapsibleStart(Title)]]`
     """
    
    def expand_macro(self, formatter, name, content):
	
	# process arguments
	args, kw = parse_args(content)
        title = ''

        for i in range(0, len(args)):
            title += args[i]

        return("<div> " +
               "<h3 class=\"foldable\">" + title + "</h3>" + 
               "<div>")

class CollapsibleEndMacro(WikiMacroBase):
    r"""CollapsibleEndMacro marks the end of a collapsible list

    Example:
    `[[CollapsibleEnd]]`
    """
    def expand_macro(self, formatter, name, content):
        return("</div></div>")
