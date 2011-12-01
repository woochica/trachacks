# -*- coding: utf-8 -*-

#TODO: add header

import re    
from datetime import datetime
from StringIO import StringIO
from trac.ticket import Milestone
from trac.util.datefmt import format_date, to_timestamp
from trac.util.html import Markup
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase

revision="$Rev$"
url="http://trac-hacks.org/wiki/PlannedMilestonesMacro"

class PlannedMilestonesMacro(WikiMacroBase):
    """
    List upcoming milestones.

    {{{
        [[PlannedMilestones()]]
	[[PlannedMilestone(N)]]
    }}}    
    """       
    def expand_macro(self, formatter, name, content):
        
        arg,kwarg = parse_args(content)
        
        includepattern = kwarg.get('include', '')
        #excludepattern = kwarg.get('exclude', '')
        length = int(kwarg.get('max', -1))
        ignorenoduedate = kwarg.get('ignore') == 'noduedate' or None
        
        if length==-1:
            length = None
        
        out = StringIO()
        
        include = re.compile(includepattern)
        #exclude = re.compile(excludepattern)

        milestones = []
        
        for milestone in Milestone.select(self.env, include_completed=False):
            if include.match(milestone.name): # and not exclude.match(milestone.name):
                milestones.append(milestone)
                
        out.write('<ul>\n')
        for milestone in milestones[0:length]:

            if milestone.due:
                #TODO: add one day to tdelta
                tdelta = (to_timestamp(milestone.due) -
                          to_timestamp(datetime.now(formatter.req.tz)))
                if tdelta > 0:
                    date = format_date(milestone.due, '%Y-%m-%d',
                                       formatter.req.tz)
                else:
                    date = None
            elif not ignorenoduedate:
                date = Markup('<i>(Unspecified)</i>')
            else:
                date = None
                
            if date:        
                out.write('<li>%s - <a href="%s">%s</a></li>\n' % 
                          (date, self.env.href.milestone(milestone.name),
                           milestone.name))
            
        out.write('</ul>\n')
        return Markup(out.getvalue())
