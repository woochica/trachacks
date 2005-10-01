# vim: expandtab
from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki import wiki_to_html
from StringIO import StringIO

import sys
import inspect
import re
import string

class ListTagsMacro(Component):
    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'ListTags'

    def get_macro_description(self, name):

        return inspect.getdoc(ListTagsMacro)

    def render_macro(self, req, name, content):
        if name == "ListTags":
           macro = ListTagsMacro()
           
        return macro.render(self,req,content)

class TagsMacro:
    def getInfo(self,db,tag,opts):
        cs = db.cursor()
        desc = tag
        linktext = tag
        # Get the latest revision only.
        cs.execute('SELECT text from wiki where name = \'%s\' order by version desc limit 1' % tag)
        csrow = cs.fetchone()
        prefix = ''

        if csrow != None:
            text = csrow[0]
            ret = re.search('=\s+([^=]*)=',text)
            if ret == None :
                    title = ''
            else :
                    title = ret.group(1)
            ret = re.search('==\s+([^=]*)==',text)
            if ret == None :
                    subtitle = ''
            else :
                    subtitle = ret.group(1)
            infos = {'pagename': tag, 'none': '', 'subtitle': subtitle, 'title': title}
            desc = infos[opts['desc']]
            linktext =  infos[opts['link']]
        else:
            prefix = "Create "

        title = StringIO()
        title.write("%s%s"%(prefix, desc))
        if prefix != '' or desc == tag:
           desc = ''

        return (linktext,title.getvalue(),desc)
    

class ListTagsMacro(TagsMacro):
    def render(self,component, req, content):
        
        self.env = component.env
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cs = db.cursor()

        tags = [ ]
        opts = {'link': 'pagename', 'desc': 'title', 'showpages': 'false'}
        if content :
            optre = re.compile("([^=]+)=(.+)")
            for tag in content.split(',') :
                opt = optre.search(tag.strip())
                if opt != None :
                   opts[opt.group(1)] = opt.group(2)
                else :
                    tags.append(tag.strip())

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        msg = StringIO()

        if tags:
            return self.wParameters(req.hdf,tags,opts,db,cursor)
        
        else:
            buf = StringIO()
            buf.write('SELECT namespace, COUNT(*) FROM wiki_namespace ')

            cursor.execute(buf.getvalue() + ' GROUP BY namespace ORDER BY namespace')

            msg.write('<ul>')
            while 1:
              row = cursor.fetchone()
              if row == None:
                 break

              tag = row[0]
              refcount = int(row[1])

              (linktext,title,desc) = self.getInfo(db,tag,opts)

              link = self.env.href.wiki(tag)

              msg.write('<li><a title="%s" href="%s">' % (title,link))
              msg.write(linktext)
              msg.write('</a> %s (%s)</li>\n' % (desc,refcount))

              if opts['showpages'] == 'true' :
                    t = [ tag ]
                    msg.write(self.wParameters(req.hdf,t,opts,db,db.cursor()))

        msg.write('</ul>')

        return msg.getvalue()

    def wParameters(self,hdf,tags,opts,db,cursor):
        buf = StringIO()
        criteria = StringIO()

        me = hdf.getValue('wiki.page_name', '')

        heirarchy = me.split('/')
        prog = re.compile('^\.([-]\d+)$')

        for current in tags:
            if current == "." :
                current = me
            else :
                m = prog.search(current)
                if m :
                    current = heirarchy[int(m.group(1))]
            buf.write('SELECT DISTINCT name FROM wiki_namespace where')
            buf.write(' namespace like \'%s\' INTERSECT ' % current)

        cursor.execute(buf.getvalue()[0:-11] + ' ORDER BY name')

        msg = StringIO()

        msg.write('<ul>')
        while 1:
            row = cursor.fetchone()
            if row == None:
                break
            tag = row[0]
            (linktext,title,desc) = self.getInfo(db,tag,opts)

            link = self.env.href.wiki(tag)

            msg.write('<li><a title="%s" href="%s">' % (title,link))
            msg.write(linktext)
            msg.write('</a> %s</li>\n' % desc)

        msg.write('</ul>')

        return msg.getvalue()
