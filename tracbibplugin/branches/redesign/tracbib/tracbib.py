"""
 tracbib/tracbib.py

 Copyright (C) 2011 Roman Fenkhuber

 Tracbib is a trac plugin hosted on trac-hacks.org. It brings support for
 citing from bibtex files in the Trac wiki from different sources.

 This file contains all Trac macros for the tracbib plugin.
 Thanks to 'runlevel0' and 'abeld' for some suggestions and bugfixes.

 tracbib is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 tracbib is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with tracbib.  If not, see <http://www.gnu.org/licenses/>.
"""

from trac.core import *
from api import *
from source import *
from formatter import *
import re
from trac.wiki.api import IWikiMacroProvider

try:
  from genshi.builder import tag
except ImportError: # for trac 0.10:
  from trac.util.html import html as tag

try:
  from trac.wiki.api import parse_args
except ImportError: # for trac 0.10:
  # following is from
  # http://trac.edgewall.org/browser/trunk/trac/wiki/api.py
  def parse_args(args, strict=True):
      """Utility for parsing macro "content" and splitting them into arguments.

      The content is split along commas, unless they are escaped with a
      backquote (like this: \,).

      :param args: macros arguments, as plain text
      :param strict: if `True`, only Python-like identifiers will be
                     recognized as keyword arguments

      Example usage:

      >>> parse_args('')
      ([], {})
      >>> parse_args('Some text')
      (['Some text'], {})
      >>> parse_args('Some text, mode= 3, some other arg\, with a comma.')
      (['Some text', ' some other arg, with a comma.'], {'mode': ' 3'})
      >>> parse_args('milestone=milestone1,status!=closed', strict=False)
      ([], {'status!': 'closed', 'milestone': 'milestone1'})

      """   
      largs, kwargs = [], {}
      if args:
          for arg in re.split(r'(?<!\\),', args):
              arg = arg.replace(r'\,', ',')
              if strict:
                  m = re.match(r'\s*[a-zA-Z_]\w+=', arg)
              else:
                  m = re.match(r'\s*[^=]+=', arg)
              if m:
                  kw = arg[:m.end()-1].strip()
                  if strict:
                      try:
                          kw = unicode(kw).encode('utf-8')
                      except TypeError:
                          pass
                  kwargs[kw] = arg[m.end():]
              else:
                  largs.append(arg)
      return largs, kwargs

  # Dummy Formatter class, Trac 0.10 only provides req
  class Formatter:
    req = None
    def __init__(self,req):
        self.req = req

from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage

class Cite(Component,dict):
    pass

class AutoLoaded(Component,dict):
    pass

from trac.web.api import IRequestFilter

class TracBibRequestFilter(Component):
    sources = ExtensionPoint(IBibSourceProvider)
    implements(IRequestFilter)

    def pre_process_request(self,req, handler):
        ''' load entries from the special wiki page 'BibTex' '''
        match = re.match(r'(^/wiki$)|(^/wiki/*)|(^/$)',req.path_info)
        if match:
            source = BibtexSourceWiki(self.env)
            if WikiPage(self.env,"BibTex").exists:
                source.source_init(req,"wiki:BibTex")
                auto = AutoLoaded(self.env)
                for key in source:
                    auto[key] = ''
        return handler

    #Trac 0.11
    def post_process_request(self,req, template, data, content_type):
        return (template,data,content_type)
    
    #Trac 0.10
    def post_process_request(self,req, template, content_type):
        return (template,content_type)


class BibAddMacro(WikiMacroBase):
    sources = ExtensionPoint(IBibSourceProvider)
    implements(IWikiMacroProvider)

    # Trac 0.10
    def render_macro(self, request,name,content):
        return self.expand_macro(Formatter(request),name,content)

    # Trac 0.11
    def expand_macro(self,formatter,name,content):
        args, kwargs = parse_args(content, strict=False)
        if len(args) != 1:
            raise TracError('[[Usage: BibAdd(source:file@rev) or BibAdd(attachment:wikipage/file) or BibAdd(attachment:file)]] ')

        arg = re.compile(":").split(args[0])
        type = arg[0]
        for source in self.sources:
            if source.source_type() == type:
                source.source_init(formatter.req,args[0])
                return
        raise TracError("Unknown container type: '"+ type +"'")

class BibCiteMacro(WikiMacroBase):
    implements(IWikiMacroProvider)
    sources = ExtensionPoint(IBibSourceProvider)
    formatter = ExtensionPoint(IBibRefFormatter)

    # Trac 0.10
    def render_macro(self, request,name,content):
        return self.expand_macro(Formatter(request),name,content)

    # Trac 0.11
    def expand_macro(self,formatter,name,content):

        args, kwargs = parse_args(content, strict=False)

        if len(args) > 1:
            raise TracError('Usage: [[BibCite(BibTexKey)]]')
        elif len(args) < 1:
            raise TracError('Usage: [[BibCite(BibTexKey)]]')

        key = args[0];

        cite = Cite(self.env)
        auto = AutoLoaded(self.env)

        if key not in cite:
            found = False
            for source in self.sources:
                if source.has_key(key):
                    found = True
                    cite[key] = source[key]
                    if auto.has_key(key):
                        del auto[key]
                    for format in self.formatter:
                        format.pre_process_entry(key,cite)
            if not found:
                raise TracError("Unknown key '"+key +"'")

        for format in self.formatter:
            entry = format.format_cite(key,cite[key])

        return entry

class BibNoCiteMacro(WikiMacroBase):
    implements(IWikiMacroProvider)
    sources = ExtensionPoint(IBibSourceProvider)
  
    # Trac 0.10
    def render_macro(self, request,name,content):
        return self.expand_macro(Formatter(request),name,content)

    # Trac 0.11
    def expand_macro(self,formatter,name,content):

        args, kwargs = parse_args(content, strict=False)

        if len(args) > 1:
            raise TracError('Usage: [[BibNoCite(BibTexKey)]]')
        elif len(args) < 1:
            raise TracError('Usage: [[BibNoCite(BibTexKey)]]')
 
        key = args[0];

        cite = Cite(self.env)
        auto = AutoLoaded(self.env)

        if key not in cite:
            found = False
            for source in self.sources:
                if source.has_key(key):
                    found = True
                    if auto.has_key(key):
                        del auto[key]
                    cite[key] = source[key]
            if not found:
                raise TracError("Unknown key '"+key +"'")
        return

class BibRefMacro(WikiMacroBase):
    formatter = ExtensionPoint(IBibRefFormatter)
    sources = ExtensionPoint(IBibSourceProvider)
    implements(IWikiMacroProvider)
    
    # Trac 0.10
    def render_macro(self, request,name,content):
        return self.expand_macro(Formatter(request),name,content)

    # Trac 0.11
    def expand_macro(self,formatter,name,content):
        cite = Cite(self.env)
        items = cite.items()

        try:
            for format in self.formatter:
                tags = format.format_ref(items,'References')
        finally:
            # CLEANUP: outdated entries might survive in memory, so clear the container
            cite.clear()
            for source in self.sources:
                source.clear()
       
        return tag.div(id='References')(*tags)

class BibFullRefMacro(WikiMacroBase):
    formatter = ExtensionPoint(IBibRefFormatter)
    sources = ExtensionPoint(IBibSourceProvider)
    implements(IWikiMacroProvider)
    
    # Trac 0.10
    def render_macro(self, request,name,content):
        return self.expand_macro(Formatter(request),name,content)
    
    # Trac 0.11
    def expand_macro(self,formatter,name,content):
        cite = Cite(self.env)
        auto = AutoLoaded(self.env)
        items = cite.items()

        try:
            for source in self.sources:
                for key,value in source.items():
                    if auto.has_key(key) and not cite.has_key(key):
                        next
                    cite[key]=value

            for format in self.formatter:
                tags = format.format_fullref(cite.items(),'Bibliography')
        finally:
            # CLEANUP: outdated entries might survive in memory, so clear the container
            cite.clear()
            for source in self.sources:
                source.clear()
       
        return tag.div(id='References')(*tags)
