# This plugin base on WikiInclude macro By Vegard Eriksen zyp at jvnv dot net.
# See: http://projects.edgewall.com/trac/wiki/MacroBazaar#WikiInclude
# Author: yu-ji
# Page version support added by bubacoo in 0.2

from __future__ import generators

try:
    from StringIO import StringIO
except ImportError:
    from StringIO import StringIO

from trac.core import *
from trac.wiki.formatter import wiki_to_html
from trac.wiki.api import IWikiMacroProvider, WikiSystem

import inspect

__all__ = ['WikiIncludeMacro']

class WikiIncludeMacro(Component):
    """
    Inserts the contents of another wiki page. It expands arguments in the page in the form {{N}}.
    
    Example:
    {{{
    [[WikiInclude(Foo)]]
    [[WikiInclude(Foo|Argument1|Argument2..|ArgumentN)]]
    }}}
    """
    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'WikiInclude'

    def get_macro_description(self, name):
        return inspect.getdoc(WikiIncludeMacro)

    def render_macro(self, req, name, txt):
	db = self.env.get_db_cnx()
	
	txt = txt or ''
	
	version = None
	
	args = txt.split('?')
	if len(args) > 1 :
		for each in args :
			if each.find("version=") > -1 :
				version = each.split('=').pop(1)	
	
	
	if version is None:
		args = txt.split('|')
		name = args.pop(0).replace('\'', '\'\'')
		sql  = "SELECT text from wiki where name = '%s' order by version desc limit 1" % name
	else:
		name = args.pop(0)
		sql  = "SELECT text from wiki where name = '%s' and version = %d " % ( name , int(version) )
	
	cs = db.cursor()
	cs.execute(sql)
	
	row = cs.fetchone()
	if row == None:
		return ''
	text = row[0]
	
	i = 0
	for arg in args:
		text = text.replace('{{%d}}' % (i+1), args[i])
		i += 1
	
	return wiki_to_html(text, self.env, req)
