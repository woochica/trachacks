__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from trac.core         import *
from trac.resource     import *

from genshi.builder    import tag
from genshi.core       import Markup
from trac.mimeview.api import IHTMLPreviewRenderer
from trac.wiki.api     import IWikiMacroProvider, parse_args
from trac.web.chrome   import ITemplateProvider, add_script
from trac.env          import IEnvironmentSetupParticipant
from trac.web.api      import IRequestFilter, IRequestHandler, RequestDone
from trac.db           import Table, Column, DatabaseManager
from tracextracturl    import extract_url
from trac.util         import md5

mindmaps = dict()

class MindMapMacro(Component):
    """
Website: http://trac-hacks.org/wiki/MindMapMacro

`$Id$`

    """
    implements ( IWikiMacroProvider, IHTMLPreviewRenderer, ITemplateProvider,
                 IRequestHandler, IRequestFilter, IEnvironmentSetupParticipant )


    SCHEMA = [
        Table('mindmapcache', key='hash')[
            Column('hash'),
            Column('content'),
        ]
    ]

    DB_VERSION = 0

    def environment_created(self):
        self._upgrade_db(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("select count(*) from mindmapcache")
            cursor.fetchone()
            return False
        except:
            db.rollback()
            return True

    def upgrade_environment(self, db):
        self._upgrade_db(db)

    def _upgrade_db(self, db):
        try:
            db_backend, _ = DatabaseManager(self.env)._get_connector()
            cursor = db.cursor()
            for table in self.SCHEMA:
                for stmt in db_backend.to_sql(table):
                    self.log.debug(stmt)
                    cursor.execute(stmt)
        except Exception, e:
            db.rollback()
            self.log.error(e, exc_info=True)
            raise TracError(unicode(e))

   # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_script( req, 'mindmap/tools.flashembed-1.0.4.min.js', mimetype='text/javascript' )
        add_script( req, 'mindmap/mindmap.js', mimetype='text/javascript' )
        return (template, data, content_type)


    def _produce_html(self, href, css, attr, flashvars):
      flashvars['initLoadFile'] = href

      return tag.div(
          tag.object(
              tag.param( name="quality", value="high" ),
              tag.param( name="bgcolor", value="#ffffff" ),
              tag.param( name="flashvars", value= Markup("&".join([ "=".join([k,unicode(v)]) for k,v in flashvars.iteritems() ]) )),
              type   = "application/x-shockwave-flash",
              **attr
          ),
          class_="mindmap",
          style=Markup(css),
      )

    def _set_cache(self, hash, content):
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      cursor.execute("INSERT INTO mindmapcache VALUES ('%s','%s')" % (hash,content) )
      db.commit()

    def _get_cache(self, hash, default=None):
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      try:
        cursor.execute('SELECT content FROM mindmapcache WHERE hash=%s', (hash,))
        (content,) = cursor.fetchone()
        return content
      except Exception, e:
        if default == None:
          raise e
        return unicode(e)

    def _check_cache(self, hash):
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      cursor.execute('SELECT count(content) FROM mindmapcache WHERE hash=%s', (hash,))
      (content,) = cursor.fetchone()
      return content

    ### methods for IWikiMacroProvider
    def get_macros(self):
      yield 'MindMap'

    def get_macro_description(self, name):
      return self.__doc__


    def expand_macro(self, formatter, name, content, args={}):
        try:
          if not args:
            args, content = content.split("\n",1)
        except: # Short macro
          largs, kwargs = parse_args( content )
          if not largs:
            raise TracError("File name missing!")
          file = largs[0]
          href = extract_url (self.env, formatter.context, file, raw=True)
        else: # Long macro
          largs, kwargs = parse_args( args )
          digest = md5()
          digest.update(unicode(content))
          hash = digest.hexdigest()
          if not self._check_cache(hash):
            mm = MindMap(content)
            self._set_cache(hash, unicode(mm))
          href = formatter.req.href.mindmap(hash + '.mm')

        attr = dict()
        attr['width']  = kwargs.pop('width',"95%")
        attr['height'] = kwargs.pop('height',"400")
        try:
          int( attr['height'] )
        except:
          pass
        else:
          attr['height'] += "px"
        try:
          int( attr['width'] )
        except:
          pass
        else:
          attr['width'] += "px"

        flashvars = {
              'openUrl'               : '_blank',
              'startCollapsedToLevel' : '5'
            };
        try:
          flashvars.update([ [k,v] for k,v in [kv.split('=') for kv in kwargs['flashvars'].strip("\"'").split('|') ] ])
        except:
          pass
        attr['data'] = formatter.context.href.chrome('mindmap','visorFreemind.swf')

        css  = ''
        if 'border' in kwargs:
          border = kwargs['border'].strip("\"'").replace(';','')
          if border == "1":
            border = "solid"
          elif border == "0":
            border = "none"
          css = 'border: ' + border

        return self._produce_html( href, css, attr, flashvars )


    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('mindmap', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

   # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/mindmap/')

    def process_request(self, req):
        if req.path_info == '/mindmap/status':
          db = self.env.get_db_cnx()
          cursor = db.cursor()
          try:
              cursor.execute('SELECT hash,content FROM mindmapcache')
              content = tag.html(tag.body(tag.dd(
                  [ [tag.dt(tag.a(k,href=req.href.mindmap(k + '.mm'))),tag.dd(tag.pre(v))] for k,v in cursor.fetchall()]
                )))
          except Exception, e:
              content = tag.html(tag.body(tag.strong("DB Error: " + unicode(e))))
          html = content.generate().render("xhtml")
          req.send_response(200)
          req.send_header('Cache-control', 'must-revalidate')
          req.send_header('Content-Type', 'text/html;charset=utf-8')
          req.send_header('Content-Length', len(html))
          req.end_headers()

          if req.method != 'HEAD':
             req.write(html)
          raise RequestDone

        try:
            hash = req.path_info[9:-3]
            req.send( self._get_cache(hash), content_type='application/x-freemind', status=200)
        except RequestDone:
            pass
        except Exception, e:
            self.log.error(e)
            req.send_response(404)
            req.end_headers()
        raise RequestDone


import re
mmline = re.compile(r"^( *)([*o+-]|\d+\.)(\([^\)]*\))?\s+(.*)$")
#mmline = re.compile(r"^( *)\*()(.*)")

class MindMap:
  "Generates Freemind Mind Map file"

  def __init__(self, tree):
    if isinstance(tree, basestring):
      tree = self.decode(tree)
    if len(tree) != 2:
      raise TracError("Tree must only have one trunk!")
    (name,branch) = tree
    self.xml = tag.map( self.node(name,branch), version="0.8.0")

  def __repr__(self):
    return self.xml.generate().render("xml")


  def node(self, name, content, args={}):
    if not content:
      return tag.node(TEXT=name,**args)
    else:
      return tag.node( [ self.node(n,c,a) for n,c,a in content ], TEXT=name, LINK=name, **args)


  def decode(self, code):
    indent = -1
    lines = code.splitlines()
    name = ''
    while not name and lines:
      name = lines.pop(0).strip()

    rec = [name, []]
    while lines:
      self._decode(rec[1], lines, indent)
    return rec

  def _decode(self, ptr, lines, indent):
    if not lines:
      return False
    if lines[0].strip() == '':
      lines.pop(0)
      return True
    m = mmline.match(lines[0])
    if not m:
      lines.pop(0)
      return False
    ind,marker,argstr,text = m.groups()
    args = self._parse_args(argstr)
    ind = len(ind)
    text = text.strip()
    if (indent == -1):
        indent = ind
    if (ind == indent):
      lines.pop(0)
      ptr.append([text, [], args])
      while self._decode(ptr, lines, ind):
        pass
      return True
    elif (ind > indent):
      lines.pop(0)
      ptr[-1][1].append( [text, [], args] )
      while self._decode(ptr[-1][1], lines, ind):
        pass
      return True
    else:
      return False

  def _parse_args(self, str):
    d = dict()
    if not str:
      return d
    for pair in str[1:-1].split(','):
      try:
        key,value = pair.split('=')
      except:
        key,value = pair,''
      key = key.strip().upper().encode()
      d[key] = value.strip()
    return d

