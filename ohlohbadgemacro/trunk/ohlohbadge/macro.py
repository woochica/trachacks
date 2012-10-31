# Created by Noah Kantrowitz on 2007-07-15.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from genshi.builder import tag 
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import system_message

class OhlohBadgeMacro(WikiMacroBase):
    """A small maco for showing Ohloh (http://ohloh.net) statistics badges."""
    
    SCRIPT_LOCATION = 'http://www.ohloh.net/p/%s/widgets/project_thin_badge'
    
    def expand_macro(self, formatter, name, content):
        content = content.strip()
        if not content.isdigit():
            return system_message('Invalid Ohloh project ID', '%s is not a number'%content)
        return tag.script('', src=self.SCRIPT_LOCATION%content, type='text/javascript')


