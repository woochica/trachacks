# -*- coding: utf-8 -*-

#
# BackLinks plugin for Trac
# Version: 6.0 - for Trac 0.11
#
# Author: Trapanator trap@trapanator.com
# Website: http://www.trapanator.com/blog/archives/category/trac
# License: GPL 3.0
#

from StringIO import StringIO
from genshi.builder import tag
from trac.wiki.macros import WikiMacroBase
import string
from trac.core import *
from trac.wiki.formatter import format_to_html
from trac.util import TracError
from trac.util.text import to_unicode
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule

class BackLinksMacro(WikiMacroBase):
    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, args):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        thispage = None
        context = formatter.context
        resource = context.resource
        if args:
                thispage = args.replace('\'', '\'\'')
        else:
                thispage = WikiPage(self.env, resource).name

        sql = 'SELECT w1.name FROM wiki w1, ' + \
                  '(SELECT name, MAX(version) AS VERSION FROM WIKI GROUP BY NAME) w2 ' + \
                  'WHERE w1.version = w2.version AND w1.name = w2.name '
        if thispage:
              sql += 'AND (w1.text LIKE \'%%[wiki:%s %%\'' % thispage
              sql += ' OR w1.text LIKE \'%%[wiki:%s]%%\'' % thispage
              if self._check_unicode_camelcase(thispage):   
                      sql += ' OR w1.text LIKE \'%%\n%s %%\'' % thispage 
                      sql += ' OR w1.text LIKE \'%% %s %%\'' % thispage 
                      sql += ' OR w1.text LIKE \'%%\n%s\r%%\'' % thispage 
                      sql += ' OR w1.text LIKE \'%% %s\r%%\'' % thispage 
              sql += ')' 

        cursor.execute(sql)
        buf = StringIO()
        buf.write('<hr style="width: 10%; padding: 0; margin: 2em 0 1em 0;"/>')
        buf.write('Pages linking to %s:\n' % thispage)
        buf.write('<ul>')
        while 1:
                row = cursor.fetchone()
                if row == None:
                        break
                s2 = thispage
                if row[0] == s2:
                        pass
                else:
                        buf.write('<li><a href="%s">' % self.env.href.wiki(row[0]))
                        buf.write(row[0])
                        buf.write('</a></li>\n')
        buf.write('</ul>')
        return buf.getvalue()

    def _check_unicode_camelcase(self, pagename): 
        if not pagename[0].isupper():   
            return False
        pagename = pagename.split('@', 1)[0].split('#', 1)[0]  
        if not pagename[-1].islower():  
            return False  
        humps = 0  
        for i in xrange(1, len(pagename)):  
            if pagename[i-1].isupper():   
                 if pagename[i].islower():  
                        humps += 1  
                 else:  
                        return False  
        return humps > 1  
