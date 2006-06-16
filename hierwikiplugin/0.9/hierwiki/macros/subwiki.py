# Macros for the HierWiki plugin

from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem

from StringIO import StringIO
import re, string, inspect

class SubWikiMacro(Component):
    """
    Inserts an alphabetic list of sub-wiki pages into the output.
    A sub-wiki page is a page that is is deeper in the hierachy than the current page.  e.g. if the current page is People, the this will return a list of all wiki entries that start with "People/"
    
    Accepts a prefix string as parameter: if provided, only pages with names that
    start with the prefix are included in the resulting list. If this parameter is
    omitted, all pages are listed.
    
    This now takes the text of the first heading and displays it as the link name.
    """

    # TODO: Everything until render_macro can be removed once switched to be based on WikiMacroBase
    implements(IWikiMacroProvider)
    
    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        name = self.__class__.__name__
        if name.endswith('Macro'):
            name = name[:-5]
        yield name
        
    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return inspect.getdoc(self.__class__)
        
    def render_macro(self, req, name, args):
        # Args seperated by commas:
        # prefix,level
        #
        # Page Name prefix to search for.
        # how many 'levels' in the hierarchy to go down.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cs = db.cursor()

        prefix = req.hdf.getValue('wiki.page_name', '') + '/'
        level = None
        if args:
            args = args.replace('\'', '\'\'')
            args = args.split(',')
            if args[0] != 'None':
                prefix = args[0]
            if len(args) > 1 and args[1] != 'None':
                level = args[1]

        sql = 'SELECT DISTINCT name FROM wiki '
        if prefix:
            sql += 'WHERE name LIKE \'%s%%\' ' % prefix
        sql += 'ORDER BY name'
        cursor.execute(sql)

        buf = StringIO()
        buf.write('<ul>')
        while 1:
            row = cursor.fetchone()
            if row == None:
                break
            name = row[0]
            if level:
                len_name = name.split('/')
                #buf.write(len_name)
                if len(len_name) > int(level)+1:
                    continue
            # Get the latest revision only.
            sql = 'SELECT name,text from wiki where name = \'%s\' order by version desc limit 1' % name
            cs.execute(sql)
            while 1:
                csrow = cs.fetchone()
                if csrow == None:
                    break
                name = csrow[0]
                text = csrow[1]
                (linktext,title,desc) = self._getinfo(db,name)

                link = self.env.href.wiki(name)

                buf.write('<li><a title="%s" href="%s">' % (title,link))
                buf.write(linktext)
                buf.write('</a> %s</li>\n' % desc)
        buf.write('</ul>')

        return buf.getvalue()

    def _getinfo(self, db, name):
        cs = db.cursor()
        desc = name
        # Get the latest revision only.
        cs.execute('SELECT text from wiki where name = \'%s\' order by version desc limit 1' % name)
        csrow = cs.fetchone()
        prefix = ''

        if csrow != None:
            text = csrow[0]
            m  = re.search('=+\s([^=]*)=+',text)
            if m != None:
                desc = string.strip(m.group(1))
        else:
            prefix = "Create "

        title = StringIO()
        title.write("%s%s"%(prefix, desc))
        if prefix != '' or desc == name:
            desc = ''

        return (name,title.getvalue(),desc)
