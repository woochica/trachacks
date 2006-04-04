'''
A wiki-processor for interpreting notes mail to wrap header pars inside a box.
The box will have a legend (dates).
'''
import re
from trac.wiki import wiki_to_html

STYLE  = 'margin-top: 2px; color:black; background-color:%s; '\
         'border: solid black 1px'
COLOR  = 'white'

def execute(hdf, txt, env):
    return parse(hdf, txt, env)

def parse(hdf, txt, env):
    txt = txt.lstrip();
    if (0 == len(txt)):
        return ""
    
    html = ""
    match = re.search(r"^(from:?\s+?)?(.*)$\s+?^(sent:?\s*)?(.*)$\s+?^to:?\s+?(.*)$\s+?^(cc:?\s+?(.*)$\s+?)?^subject:?\s+(.*)$", txt, re.IGNORECASE | re.MULTILINE)
    if match:
        if (-1 == match.start(1)):
            pre_content = match.string[0:match.start(2)]
        else:
            pre_content = match.string[0:match.start(1)]
        from1 = match.group(2)
        date = match.group(4)
        to = match.group(5)
        if (-1 != match.start(6)) and (-1 != match.start(7)):
            cc = match.group(7)
        else:
            cc = ''
        subject = match.group(8)
        content = match.string[match.end(8):]
    else:
        return wiki_to_html(txt, env, hdf, env.get_db_cnx(), escape_newlines=True)
    
    html = '%s<br />'\
           '<fieldset style="%s">'\
           '<legend style="%s">%s</legend>'\
           'From: %s<br />'\
           'To: %s<br />' % (wiki_to_html(pre_content, env, hdf, env.get_db_cnx(), escape_newlines=True), 
                             STYLE, 
                             STYLE, 
                             date, 
                             from1.replace("<", "&lt;"), 
                             to.replace("<", "&lt;"))
    
    if (0 < len(cc)):
        html += 'Cc: %s<br />' % cc.replace("<", "&lt;")
    
    html += 'Subject: %s<br />'\
            '</fieldset><br />'\
            '%s<br />' % (subject, 
                          parse(hdf, content, env))
    
    return html
