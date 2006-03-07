"""
Reference section headers in the current page. To refer to the section
[[ref(Using Macros)]], use

{{{
[[ref(Using Macros)]]
}}}

"""
import re
from trac.wiki.formatter import Formatter

def execute(hdf, args, env):
	return "<a href='#%s' title='Jump to section %s'>%s</a>" % (Formatter._anchor_re.sub("", args), args.replace("'", "\\'"), args)
