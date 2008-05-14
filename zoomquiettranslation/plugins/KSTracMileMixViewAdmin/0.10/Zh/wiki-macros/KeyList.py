"""
usage: [[KeyList]]
"""

import re
import string

## default style values
styles = { "background": "#",
           "width": "60%",
           }


def execute(hdf, txt, env):

    # get trac.ini
    projectName = env.config.get('project', 'name')
    view_url = "/%s/%s" % (projectName, "keylist")

    db = env.get_db_cnx()
    curs = db.cursor()
    option = {}
    ul = []
    
    try:
        curs.execute("SELECT milestone FROM rt_template")
        reAllMilestone = [m[0] for m in curs.fetchall()]

        # strip milestone name
        milestone = []
        for m in reAllMilestone:
            mm = []
            for s in m.split("."):
                try:
                    s.encode("ascii")
                    mm.append(s)
                except:
                    break
            milestone.append(".".join(mm))

        for m, m_full in zip(milestone, reAllMilestone):
            filename = "idx-%s.html" % m
            href = "%s/%s" % (view_url, filename)
            ul.append('<li><a href="%s" title="%s">%s</a></li>' % (href, m_full, m_full))

    except Exception, e:
        return 'error: %s %s' % (Exception, e)

    return '''
<fieldset class="keylist" style="background: #f7f7f0; width:80%%;">
    <legend>Keylist:</legend>
    <ul>
    %s
    </ul>
</fieldset>
''' % ("\n".join(ul))


