"""
Display list of ticket numbers in a box on the right side of the page.
The purpose of this macro is show related tickets compactly.
You can specify ticket number or report number which would be expanded
as ticket numbers. Tickets will be displayed as sorted and uniq'ed.

Example:
{{{
[[TicketBox(#1,#7,#31)]]               ... list of tickets
[[TicketBox(1,7,31)]]                  ... '#' char can be omitted
[[TicketBox({1})]]                     ... expand report result as ticket list
[[TicketBox([report:1])]]              ... alternate format of report
[[TicketBox([report:9?name=val])]]     ... report with dynamic variable
[[TicketBox({1),#50,{2},100)]]         ... convination of above
[[TicketBox(500pt,{1})]]               ... with box width as 50 point
[[TicketBox(200px,{1})]]               ... with box width as 200 pixel
[[TicketBox(25%,{1})]]                 ... with box width as 25%
[[TicketBox('Different Title',#1,#2)]] ... Specify title
[[TicketBox(\"Other Title\",#1,#2)]]     ... likewise
[[TicketBox('%d tickets',#1,#2)]]      ... embed ticket count in title
[[TicketBox({1}, nosort)]]             ... display numbers without sort
}}}

[wiki:TracReports#AdvancedReports:DynamicVariables Dynamic Variables] 
is supported for report. Variables can be specified like
{{{[report:9?PRIORITY=high&COMPONENT=ui]}}}. Of course, the special
variable '{{{$USER}}}' is available. The login name (or 'anonymous)
is used as $USER if not specified explicitly.
"""

## NOTE: CSS2 defines 'max-width' but it seems that only few browser
##       support it. So I use 'width'. Any idea?

import re
import string
from trac.wiki.formatter import wiki_to_oneliner
from trac.ticket.report import ReportModule

## Mock request object
class MockReq(object):
    def __init__(self):
        self.hdf = dict()
        self.authname = 'anonymous'

## default style values
styles = { "float": "right",
           "background": "#f7f7f0",
           "width": "25%",
           }
inline_styles = { "background": "#f7f7f0", }

args_pat = [r"#?(?P<tktnum>\d+)",
            r"{(?P<rptnum>\d+)}",
            r"\[report:(?P<rptnum2>\d+)(?P<dv>\?.*)?\]",
            r"(?P<width>\d+(pt|px|%))",
            r"(?P<keyword>nosort|summary|inline)",
            r"(?P<title1>'.*')",
            r'(?P<title2>".*")']

def uniq(x):
    y=[]
    for i in x:
        if not y.count(i):
            y.append(i)
    return y

def sqlstr(x):
    """Make quoted value string for SQL."""
    return "'%s'" % x.replace( "'","''" )

def execute(hdf, txt, env):
    if not txt:
        txt = ''
    items = []
    summaries = {}
    show_summary = False
    inline = False
    nosort = False
    title = "Tickets"
    args_re = re.compile("^(?:" + string.join(args_pat, "|") + ")$")
    for arg in [string.strip(s) for s in txt.split(',')]:
        match = args_re.match(arg)
        if not match:
            env.log.debug('TicketBox: unknown arg: %s' % arg)
            continue
        elif match.group('title1'):
            title = match.group('title1')[1:-1]
        elif match.group('title2'):
            title = match.group('title2')[1:-1]
        elif match.group('width'):
            styles['width'] = match.group('width')
        elif match.group('tktnum'):
            items.append(int(match.group('tktnum')))
        elif match.group('keyword'):
            kw = match.group('keyword').lower()
            if kw == 'summary':
                show_summary = True
            elif kw == 'inline':
                inline = True
            elif kw == 'nosort':
                nosort = True
        elif match.group('rptnum') or match.group('rptnum2'):
            num = match.group('rptnum') or match.group('rptnum2')
            dv = {}
            # username, do not override if specified
            if not dv.has_key('USER'):
                dv['USER'] = hdf.getValue('trac.authname', 'anonymous')
            if match.group('dv'):
                for expr in string.split(match.group('dv')[1:], '&'):
                    k, v = string.split(expr, '=')
                    dv[k] = v
            #env.log.debug('dynamic variables = %s' % dv)
            db = env.get_db_cnx()
            curs = db.cursor()
            req = MockReq()
            try:
                curs.execute('SELECT sql FROM report WHERE id=%s' % num)
                (query,) = curs.fetchone()
                # replace dynamic variables with sql_sub_vars()
                # NOTE: sql_sub_vars() takes different arguments in
                #       several trac versions.
                #       For 0.10 or before, arguments are (req, query, args)
                #       For 0.10.x, arguments are (req, query, args, db)
                #       For 0.11 or later, arguments are (query, args, db)
                query, dv = ReportModule(env).sql_sub_vars(req, query, dv)
                #env.log.debug('query = %s' % query)
                curs.execute(query, dv)
                rows = curs.fetchall()
                if rows:
                    descriptions = [desc[0] for desc in curs.description]
                    idx = descriptions.index('ticket')
                    summ = descriptions.index('summary')
                    for row in rows:
                        items.append(row[idx])
                        summaries[row[idx]] = row[summ]
            finally:
                if not hasattr(env, 'get_cnx_pool'):
                    # without db connection pool, we should close db.
                    curs.close()
                    db.close()
    items = uniq(items)
    if not nosort:
        items.sort()
    html = ''

    if show_summary:
        html = string.join([wiki_to_oneliner("%s (#%d)" % (summaries[n], n),
                                             env, env.get_db_cnx()) for n in items], "<br>")
    else:
        html = wiki_to_oneliner(string.join(["#%d" % c for c in items], ", "),
                                env, env.get_db_cnx())

    if html != '':
        try:
            title = title % len(items)  # process %d in title
        except:
            pass
        if inline:
            style = string.join(["%s:%s" % (k,v) for k,v in inline_styles.items() if v <> ""], "; ")
        else:
            style = string.join(["%s:%s" % (k,v) for k,v in styles.items() if v <> ""], "; ")
        return '<fieldset class="ticketbox" style="%s"><legend>%s</legend>%s</fieldset>' % \
               (style, title, html)
    else:
        return ''
