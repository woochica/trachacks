__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from trac.core import *
from trac.resource import *

from genshi.builder import tag
from genshi.core import Markup
from trac.mimeview.api import IHTMLPreviewRenderer
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.web.chrome import ITemplateProvider
from  trac.web.api     import  IRequestFilter, IRequestHandler, RequestDone
from tracextracturl import *
from trac.util import md5

from  ast  import literal_eval

mindmaps = dict()

class MindMapMacro(Component):
    """
Website: http://trac-hacks.org/wiki/MindMapMacro

`$Id$`

    """
    implements(IWikiMacroProvider, IHTMLPreviewRenderer, ITemplateProvider)
    implements ( IRequestHandler)


    def _produce_html(self, data):
      """ Awaits data as dictionary and returns a genshi HTML tag. """
      return tag.div(
          tag.object(
              tag.param( name="quality", value="high" ),
              tag.param( name="bgcolor", value="#ffffff" ),
              tag.param( name="flashvars", 
                value="openUrl=_blank&initLoadFile=%(href)s&startCollapsedToLevel=5" % data ),
              type="application/x-shockwave-flash",
              data="%(site)s/visorFreemind.swf" % data,
              width="%(width)s" % data,
              height="%(height)s" % data,
          ),
          class_="freemindmap",
          style="width:%(width)s; height:%(height)s" % data,
      )

    ### methods for IWikiMacroProvider
    def get_macros(self):
      yield 'MindMap'

    def get_macro_description(self, name):
      return self.__doc__

    def expand_macro(self, formatter, name, content, args={}):
        mm = "<N/A>"
        if not args:
          try:
            args, content = content.split("\n",1)
            largs, kwargs = parse_args( args )
            #content = literal_eval ( content )
            digest = md5()
            digest.update(unicode(content))
            hash = digest.hexdigest()
            mm = MindMap(content)
            mindmaps[hash] = mm
          except Exception, e:
            return str(e)
            largs, kwargs = parse_args( content )
        else:
          return 'no args'
          largs, kwargs = [], args

        #return 'MM: ' + unicode(mm)

        #href = extract_url (self.env, formatter.context, file, raw=True)
        #site = unicode( formatter.context.href.chrome('mindmap') )
        #return  unicode(tag.pre(mm)) +
        return  """<div style="width: 85%%; height: 500px;"
        class="freemindmap"><object width="85%%" height="500px"
        data="/sqlite/chrome/mindmap/visorFreemind.swf"
        type="application/x-shockwave-flash"><param value="high"
        name="quality"/><param value="#ffffff" name="bgcolor"/><param
        value="openUrl=_blank&amp;startCollapsedToLevel=3&amp;initLoadFile=%s"
        name="flashvars"/></object></div>""" % formatter.req.href.mindmap(hash)

        return tag.div( 
            tag.pre ( "Args: " + unicode(args) ),
            tag.pre ( "Content: " + unicode(content) ),
            tag.pre ( "LArgs: " + unicode(largs) ),
            tag.pre ( "KwArgs: " + unicode(kwargs) ),
            tag.pre ( "MindMap: " + unicode(mindmaps)),
            tag.pre ( "MindMap: ", tag.a(hash, href=formatter.req.href.mindmap(hash) ) ),
          )

        return self._produce_html( { 'width':width, 'height':height, 
          'href':href, 'site':site } )


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
        try:
            hash = req.path_info[9:]
            req.send( unicode(mindmaps.pop(hash)), content_type='text/css', status=200)
        except RequestDone:
            pass
        except Exception, e:
            self.log.error(e)
            req.send_response(404)
            req.end_headers()
        raise RequestDone


import re
mmline = re.compile(r"^( *)\*(\([^\)]*\))?\s*(.*)$")
#mmline = re.compile(r"^( *)\*()(.*)")

class MindMap:
  "Generates Freemind Mind Map file"

  def __init__(self, tree):
    if isinstance(tree, basestring):
      tree = self.decode(tree)
    if len(tree) != 2:
      raise TracError("Tree must only have one trunk!")
    (name,branch) = tree
    self.xml = tag.map( self.node(name,branch), version="0.9.0")

  def __repr__(self):
    return self.xml.generate().render("xml")


  def node(self, name, content, args={}):
    if not content:
      return tag.node(TEXT=name,**args)
    else:
      return tag.node( [ self.node(n,c,a) for n,c,a in content ], TEXT=name, **args)


  def decode(self, code):
    indent = 1
    lines = code.splitlines()
    rec = [lines.pop(0), []]
    while lines:
      self._decode(rec[1], lines, indent)
    return rec

  def _decode(self, ptr, lines, indent):
    if not lines:
      return False
    if lines[0].strip() == '':
      return True
    m = mmline.match(lines[0])
    if not m:
      lines.pop(0)
      return False
    ind,argstr,text = m.groups()
    args = self._parse_args(argstr)
    ind = len(ind)
    text = text.strip()
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

