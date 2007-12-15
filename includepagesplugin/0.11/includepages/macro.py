from genshi.builder import Element, tag
from genshi.core import Markup

from trac.core import *
from trac.wiki.formatter import format_to_html
from trac.wiki.api import IWikiMacroProvider, WikiSystem

import inspect

__all__ = ['IncludePagesMacro']

class IncludePagesMacro(Component):
    """
    Inserts the contents of another wiki page. It takes one mandatory
    item and two optional positional items.  The mandatory item is the
    page name.  The optional items are the class of the generated
    heading and the class of the div surrounding the included page.
    If the first positional item is missing, no heading will be
    generated.  If the second is missing, no div will be generated.
    
    Example:
    {{{
    [[IncludePages(Foo)]]
    [[IncludePages(Foo,headclass)]]
    [[IncludePages(Foo,headclass,blockclass)]]
    }}}
    """
    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'IncludePages'

    def get_macro_description(self, name):
        return inspect.getdoc(IncludePagesMacro)

    def expand_macro(self, formatter, name, txt):
	db = self.env.get_db_cnx()


	txt = txt or ''
	args = txt.split(',')

        # strip off quotes and re markers 
        pagename = args[0].replace('"','')
        pagename = pagename.replace('$','')
        pagename = pagename.replace('^','')

        # get the page
        sql  = "SELECT text from wiki where name = '%s' order by version desc limit 1" % pagename
	cs = db.cursor()
	cs.execute(sql )
	
	row = cs.fetchone()
	if row == None:
		return ''
	text = row[0]

        # put in the heading if a style is provided
        if len(args) == 3:
            return tag.div(class_=args[2])(
                                tag.div(class_=args[1])(pagename),
                                format_to_html(self.env,
                                               formatter.context,
                                               text)
                                )
        if len(args) == 2:
            return tag.div(tag.div(class_=args[1])(pagename),
                           format_to_html(self.env,
                                          formatter.context,
                                          text)
                           )
        else:
            return format_to_html(self.env, formatter.context, text)


