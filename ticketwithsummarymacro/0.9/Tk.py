"""
It shows ticket and summary

Example:
{{{
[[Tk(#1,#7,#31)]]               
}}}
"""

import re
import string

## default style values
styles = { "float": "right",
           "background": "#FFFFFF",
           "width": "25%",
           }

args_pat = [r"#?(?P<tktnum>\d+)",
            r"{(?P<rptnum>\d+)}"]

def uniq(x):
    y=[]
    for i in x:
        if not y.count(i):
            y.append(i)
    return y

def execute(hdf, txt, env):
    if not txt:
        txt = ''
    items = []
    msgs = []
    title = ""
    args_re = re.compile("^(?:" + string.join(args_pat, "|") + ")$")
    for arg in [string.strip(s) for s in txt.split(',')]:
        match = args_re.match(arg)
        if not match:
            env.log.debug('Tk: unknown arg: %s' % arg)
            continue
        elif match.group('tktnum'):
            items.append(int(match.group('tktnum')))
            db = env.get_db_cnx()
            curs = db.cursor()
            try:
                curs.execute('SELECT summary FROM ticket WHERE id=%s' % match.group('tktnum'))
                row = curs.fetchone()
                if row:
                    summary = row[0]
                    msgs.append("#%d : %s" % (int(match.group('tktnum')), summary))

            finally:
                if not hasattr(env, 'get_cnx_pool'):
                    # without db connection pool, we should close db.
                    curs.close()
                    db.close()
        
    html = ''
    try:
        # for trac 0.9 or later
        from trac.wiki.formatter import wiki_to_oneliner
        for b in msgs :
            html += wiki_to_oneliner(string.join(["%s" % b ]), env, env.get_db_cnx())
            html += '<br>'
    except:
        # for trac 0.8.x
        from trac.WikiFormatter import wiki_to_oneliner
        html = wiki_to_oneliner(string.join(["#%d" % c for c in items], ", "),
                                hdf, env, env.get_db_cnx())
    if html != '':
        try:
            title = title % len(items)  # process %d in title
        except:
            pass
        style = string.join(["%s:%s" % (k,v) for k,v in styles.items() if v <> ""], "; ")
        return '%s' %  (html)
    else:
        return ''


