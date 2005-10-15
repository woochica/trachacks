# vim: expandtab
from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki import wiki_to_html
from trac.env import IEnvironmentSetupParticipant
from trac.web.main import IRequestHandler
from StringIO import StringIO

import sys
import inspect
import re
import string

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
    
class ListTags(TagsMacro):
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

class TagCloud(TagsMacro):
    def render(self,component, req, content):
        self.env = component.env
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cs = db.cursor()

        opts = { 'smallest' : 10, 'biggest' : 22}
        
        if content :
            optre = re.compile("([^=]+)=(.+)")
            for tag in content.split(',') :
                opt = optre.search(tag.strip())
                if opt != None :
                   opts[opt.group(1)] = opt.group(2)

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        msg = StringIO()

        buf = StringIO()
        buf.write('SELECT namespace, COUNT(*) FROM wiki_namespace ')

        cursor.execute(buf.getvalue() + ' GROUP BY namespace ORDER BY namespace')

        minimum = 10000
        maximum = 0
        tags = { }

        while 1:
              row = cursor.fetchone()
              if row == None:
                 break

              tag = row[0]
              refcount = int(row[1])

              tags[tag] = refcount

              if refcount < minimum :
                 minimum = refcount
              if refcount > maximum :
                 maximum = refcount

        r = maximum - minimum + 1

        smallest = float(opts['smallest'])
        biggest = float(opts['biggest'])

        slots = (biggest - smallest) + 1

        mult = float(slots)/float(r)

        keys = tags.keys()
        keys.sort(lambda x, y: cmp(x, y))
        first = True
        for tag in keys :
            count = tags[tag]
            size = smallest + ((count - minimum)* mult)

            if first is False :
                msg.write(", ")
            else :
                first = False
            msg.write("<span style=\"font-size:%spx\">" % (size))
            (linktext,title,link) = (tag,tags[tag],self.env.href.wiki(tag))
            msg.write('<a rel=\"tag\" href="%s">' % (link))
            msg.write(linktext)
            msg.write('</a> </span> (%s)' % (count))
        return msg.getvalue()

class TagIt(TagsMacro):
    def render(self,component, req, content):
        self.env = component.env
        db = self.env.get_db_cnx()
        cursor = db.cursor()

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

        current = req.hdf.getValue('wiki.page_name', '')

        sql = 'DELETE FROM wiki_namespace where name = \'%s\' ' % current
        cursor.execute(sql)

        buf = StringIO()

        for tag in tags:
            if (tag != ""):
               sql = 'INSERT INTO wiki_namespace(name,namespace) values(\'%s\',\'%s\')' % (current,tag)
               cursor.execute(sql)

        db.commit()

        buf.write('SELECT namespace FROM wiki_namespace WHERE wiki_namespace.name=\'%s\' ORDER by namespace' % current)

        cursor.execute(buf.getvalue())

        msg = StringIO()
        msg.write("Tags:")

        count = 0;

        while 1:
            row = cursor.fetchone()
            if row == None:
                break

            tag = row[0]
            (linktext,title,desc) = self.getInfo(db,tag,opts)

            link = self.env.href.wiki(tag)

            count = count + 1
            msg.write('<a title="%s" href="%s" rel="tag">' % (title, link))
            msg.write(linktext)
            msg.write('</a> \n')

        if (count > 0):
            return (msg.getvalue()[0:-2] + ('.'))
        else:
            return ""

class ListTagsMacro(Component):
    implements(IWikiMacroProvider)

    __tag_macros = {
        'ListTags' : ListTags,
        'TagCloud' : TagCloud,
        'TagIt' : TagIt,
    }

    def get_macros(self):
        return self.__tag_macros.keys()

    def get_macro_description(self, name):
        return inspect.getdoc(self.__tag_macros[name])

    def render_macro(self, req, name, content):
        macro = self.__tag_macros[name]()
        return macro.render(self, req, content)

class SetupTags(Component):
    implements(IEnvironmentSetupParticipant)

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("select count(*) from wiki_namespace")
            cursor.fetchone()
        except:
            return True

    def upgrade_environment(self, db):
        cursor = db.cursor()

        sql = 'CREATE TABLE wiki_namespace(name text,namespace text)'
        cursor.execute(sql)

        sql = 'CREATE INDEX wiki_namespace_idx on wiki_namespace(name,namespace);'
        cursor.execute(sql)

        db.commit()

class TagsLi(Component):
    implements(IRequestHandler)
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/tagli'
                
    def process_request(self, req):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cs = db.cursor()
        tag = req.args.get('tag')
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.end_headers()
        buf = StringIO()
        if tag:
            buf.write('WHERE namespace LIKE \'%s%s\'' % (tag,'%'))
            
        cursor.execute('SELECT DISTINCT namespace FROM wiki_namespace %s ORDER BY namespace' % (buf.getvalue()))

        msg = StringIO()

        msg.write('<ul>')
        while 1:
            row = cursor.fetchone()
            if row == None:
                 break

            t = row[0]
            msg.write('<li>')
            msg.write(t)
            msg.write('</li>')

        msg.write('</ul>')

        req.write(msg.getvalue())        
