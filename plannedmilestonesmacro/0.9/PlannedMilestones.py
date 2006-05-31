from StringIO import StringIO
from trac.util import Markup, format_date
from trac.ticket import Milestone

def execute(hdf, txt, env):
    out = StringIO()
    out.write('<ul>\n')
    for milestone in Milestone.select(env, include_completed=False):
        if milestone.due > 0:
            date = format_date(milestone.due)
        else:
            date = Markup('<i>(later)</i>')
        out.write(Markup('<li>%s - <a href="%s">%s</a></li>\n',
                         date, env.href.milestone(milestone.name),
                         milestone.name))
    out.write('</ul>\n')
    return out.getvalue()
