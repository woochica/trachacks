# -*- coding: utf-8 -*-
import os
import re

from trac.config import ExtensionOption, ExtensionPoint
from trac.core import *
from trac.ticket.query import Query
from trac.util import TracError
from trac.wiki.macros import WikiMacroBase
from trac.web.href import Href
from trac.wiki import Formatter

class ProjectLoopMacro(WikiMacroBase):
    """Progress wiki macro plugin for Trac
    """

    def expand_macro(self, formatter, name, text, args):
        projects_dir = args.get('path', os.environ.get('TRAC_ENV_PARENT_DIR', '/env/trac/projects'))
	match = args.get('match', '.*')
	rawhtml = args.get('rawhtml', 'false')
	
	if not os.path.isdir(projects_dir):
	  return sys.stderr
	
        from StringIO import StringIO
        out = StringIO()
	
	for f in os.listdir(projects_dir):
	  project_dir = projects_dir + '/'+ f
	  if os.path.isdir(project_dir) and f != '.egg-cache' and re.match(match,f):
	    from trac.env import open_environment
	    selfenv = open_environment(project_dir)

	    import copy
	    context = copy.copy(formatter.context)
	    href = '/projects/' + f + '/'
	    context.href = Href(href)
	    context.req.href = context.href
	    
	    wikitext = text
	    wikitext = wikitext.replace('$dir',project_dir)
	    wikitext = wikitext.replace('$basedir',f)
	    wikitext = wikitext.replace('$name',selfenv.project_name)
	    wikitext = wikitext.replace('$href', href)
	    if rawhtml == 'false':
	      Formatter(selfenv, context).format(wikitext, out)
	    else:
	      out.write(wikitext)
	    
        return out.getvalue()
