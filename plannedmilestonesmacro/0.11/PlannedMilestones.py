# -*- coding: utf-8 -*-
# http://www.trac-hacks.org/wiki/PlannedMilestonesMacro

import re    
from datetime import datetime, tzinfo
from trac.wiki.macros import WikiMacroBase
from trac.util.datefmt import format_datetime, utc, to_timestamp
from StringIO import StringIO
from trac.wiki.formatter import Formatter
from genshi.core import Markup
from genshi.builder import tag
from trac.ticket import Milestone

revision="$Rev"
url="$URL"

class PlannedMilestonesMacro(WikiMacroBase):
    """
    List upcoming milestones.

    {{{
        [[PlannedMilestones()]]
	[[PlannedMilestone(N)]]
    }}}    
    """       
    def expand_macro(self, formatter, name, content):
        
        length = None
        pattern = ''
        
        if content:
            argv = [arg.strip() for arg in content.split(',')]
            if len(argv) > 0:
                pattern = argv[0]
            if len(argv) > 1:
                length = int(argv[1])
                
        out = StringIO()
        out.write('<ul>\n')
        
        milestones = []
        
        for milestone in Milestone.select(self.env, include_completed=False):
            if re.match(pattern, milestone.name):
                milestones.append(milestone)
                
        for milestone in milestones[0:length]:

            if milestone.due:
                tdelta = to_timestamp(milestone.due) - to_timestamp(datetime.now(utc))
                if tdelta > 0:
                    date = format_datetime(milestone.due, '%Y-%m-%d')
                else:
                    date = None
            else:
                date = Markup('<i>(Unspecified)</i>')
                
            if date:        
                out.write('<li>%s - <a href="%s">%s</a></li>\n' % (date, self.env.href.milestone(milestone.name), milestone.name))
            
        out.write('</ul>\n')
        return Markup(out.getvalue())
