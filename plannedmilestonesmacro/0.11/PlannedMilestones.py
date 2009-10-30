# -*- coding: utf-8 -*-
revision = "$Rev: 102 $"
url = "$URL: https://kunlun.shijinet.cn/svn/Trac/Macro/0.11/PlannedMilestonesMacro.py $"
    
from trac.wiki.macros import WikiMacroBase
from trac.util.datefmt import format_datetime, utc, to_timestamp
from StringIO import StringIO
from trac.wiki.formatter import Formatter
from genshi.core import Markup
from genshi.builder import tag
from trac.ticket import Milestone

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

        if content:
            argv = [arg.strip() for arg in content.split(',')]
            if len(argv) > 0:
                length = int(argv[0])
	
        out = StringIO()
        out.write('<ul>\n')
        milestones = Milestone.select(self.env, include_completed=False)
	for milestone in milestones[0:length]:
            if to_timestamp(milestone.due) > 0:
                date = format_datetime(milestone.due, '%Y-%m-%d')
            else:
                date = Markup('<i>(later)</i>')
            out.write('<li>%s - <a href="%s">%s</a></li>\n' % (date, self.env.href.milestone(milestone.name), milestone.name))
            
        out.write('</ul>\n')
        return Markup(out.getvalue())
