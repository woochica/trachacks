from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.util import Markup
from trac.wiki import wiki_to_html
from StringIO import StringIO
from tractags.api import TagEngine, ITagSpaceUser
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
            buf.write('SELECT tag, COUNT(*) FROM tags WHERE tags.tagspace = \'wiki\'')

            cursor.execute(buf.getvalue() + ' GROUP BY tag ORDER BY tag')

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
            buf.write('SELECT DISTINCT name FROM tags WHERE')
            buf.write(' tagspace = \'wiki\' AND tag LIKE \'%s\' INTERSECT ' % current)

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

#class TagCloud(TagsMacro):
#    def render(self,component, req, content):
#        self.env = component.env
#        db = self.env.get_db_cnx()
#        cursor = db.cursor()
#        cs = db.cursor()
#
#        opts = { 'smallest' : 10, 'biggest' : 22}
#        
#        if content :
#            optre = re.compile("([^=]+)=(.+)")
#            for tag in content.split(',') :
#                opt = optre.search(tag.strip())
#                if opt != None :
#                   opts[opt.group(1)] = opt.group(2)
#
#        db = self.env.get_db_cnx()
#        cursor = db.cursor()
#        msg = StringIO()
#
#        buf = StringIO()
#        buf.write('SELECT tag, COUNT(*) FROM tags WHERE tagspace = \'wiki\'')
#
#        cursor.execute(buf.getvalue() + ' GROUP BY tag ORDER BY tag')
#
#        minimum = 10000
#        maximum = 0
#        tags = { }
#
#        while 1:
#              row = cursor.fetchone()
#              if row == None:
#                 break
#
#              tag = row[0]
#              refcount = int(row[1])
#
#              tags[tag] = refcount
#
#              if refcount < minimum :
#                 minimum = refcount
#              if refcount > maximum :
#                 maximum = refcount
#
#        r = maximum - minimum + 1
#
#        smallest = float(opts['smallest'])
#        biggest = float(opts['biggest'])
#
#        slots = (biggest - smallest) + 1
#
#        mult = float(slots)/float(r)
#
#        keys = tags.keys()
#        keys.sort(lambda x, y: cmp(x, y))
#        first = True
#        for tag in keys :
#            count = tags[tag]
#            size = smallest + ((count - minimum)* mult)
#
#            if first is False :
#                msg.write(", ")
#            else :
#                first = False
#            msg.write("<span style=\"font-size:%spx\">" % (size))
#            (linktext,title,link) = (tag,tags[tag],self.env.href.wiki(tag))
#            msg.write('<a rel=\"tag\" href="%s">' % (link))
#            msg.write(linktext)
#            msg.write('</a> </span> (%s)' % (count))
#        return msg.getvalue()

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

        sql = 'DELETE FROM tags where name = \'%s\' AND tagspace = \'wiki\' ' % current
        cursor.execute(sql)

        buf = StringIO()

        for tag in tags:
            if (tag != ""):
               sql = 'INSERT INTO tags(tagspace,name,tag) values(\'wiki\', \'%s\',\'%s\')' % (current,tag)
               cursor.execute(sql)

        db.commit()

        buf.write('SELECT tag FROM tags WHERE tagspace=\'wiki\' AND name=\'%s\' ORDER by tag' % current)

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

class WikiTagsMacro(Component):
    implements(IWikiMacroProvider)

    __tag_macros = {
        'ListTags' : ListTags,
        #'TagCloud' : TagCloud,
        'TagIt' : TagIt,
    }

    def get_macros(self):
        return self.__tag_macros.keys()

    def get_macro_description(self, name):
        return inspect.getdoc(self.__tag_macros[name])

    def render_macro(self, req, name, content):
        macro = self.__tag_macros[name]()
        return macro.render(self, req, content)

class TagCloudMacro(Component):
    """ Display a summary of all tags, with the font size reflecting the number
        of pages the tag applies to. Font size ranges from 10 to 22 pixels, but
        this can be overridden by the smallest=n and biggest=n macro parameters.
    """

    implements(IWikiMacroProvider, ITagSpaceUser)

    # ITagSpaceUser methods
    def tagspaces_used(self):
        yield 'wiki'

    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'TagCloud'

    def get_macro_description(self, name):
        return pydoc.getdoc(self)

    def render_macro(self, req, name, content):
        range = (10, 22)
        if content:
            args = dict([(k.strip(), v.strip()) for k, v in [x.split('=') for x in content.split(',')]])
            range = (int(args.get('smallest', range[0])), int(args.get('biggest', range[1])))
        # Get wiki tagspace
        tags = TagEngine(self.env).wiki
        cloud = {}
        min, max = 9999, 0
        for tag in tags.get_tags():
            count = tags.count_tagged_names(tag)
            cloud[tag] = count
            if count < min: min = count
            if count > max: max = count
        names = cloud.keys()
        names.sort()
        rlen = float(range[1] - range[0])
        tlen = float(max - min)
        scale = 1.0
        if tlen:
            scale = rlen / tlen
        out = []
        for name in names:
            out.append('<a rel="tag" style="font-size: %ipx" href="%s">%s</a> (%i)' % (
                       range[0] + int((cloud[name] - min) * scale),
                       self.env.href.wiki(name),
                       name,
                       cloud[name]
                       ))
        return ', '.join(out)
