"""
Reference section headers in the current page. To refer to the section
[[ref(Using Macros)]], use

{{{
[[ref(Using Macros)]]
}}}

"""
from trac.wiki.formatter import Formatter

def execute(hdf, args, env):
    anchor = Formatter._anchor_re.sub("", args) 
    if not anchor or not anchor[0].isalpha(): 
        anchor = 'a' + anchor 
    return "<a href='#%s' title='Jump to section %s'>%s</a>" % \ 
        (anchor, args.replace("'", "\\'"), args) 
