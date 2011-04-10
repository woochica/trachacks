from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from helper import def_strings, replace_tags
try:
  from trac.wiki.api import parse_args
except ImportError: # for trac 0.10:
  import re
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

from trac.wiki.macros import WikiMacroBase
from trac.attachment import Attachment
try:
  from genshi.builder import tag
except ImportError: # for trac 0.10:
  from trac.util.html import html as tag
from trac.wiki.model import WikiPage
from trac.wiki.formatter import WikiProcessor
from trac.util.html import escape
from genshi import Markup

import re
import bibtexparse

BIBDB = 'bibtex - database'
CITELIST = 'referenced elements'

BIBTEX_KEYS = [
    'author',
    'editor',
    'title',
    'intype',
    'booktitle',
    'edition',
   'doi',
    'series',
    'journal',
    'volume',
    'number',
    'organization',
    'institution',
    'publisher',
    'school',
    'howpublished',
    'day',
    'month',
    'year',
    'chapter',
    'volume',
    'paper',
    'type',
    'revision',
    'isbn',
    'pages',
]
def extract_entries(text):
  strings,bibdb=bibtexparse.bibtexload(text.splitlines())
  for k,bib in bibdb.iteritems():
      bibtexparse.replace_abbrev(bib,def_strings)
      bibtexparse.replace_abbrev(bib,strings)
      for key,value in bib.iteritems() :
        bib[key] = replace_tags(value)
  return bibdb

class BibAddMacro(WikiMacroBase):
  implements(IWikiMacroProvider)

  def render_macro(self, request,name,content):
    return self.expand_macro(request,name,content)

  def expand_macro(self,formatter,name,content):
    args, kwargs = parse_args(content, strict=False)
    if len(args) != 1:
      raise TracError('[[Usage: BibAdd(source:file@rev) or BibAdd(attachment:wikipage/file) or BibAdd(attachment:file)]] ')
    
    whom = re.compile(":|@").split(args[0])
    file = None
    rev = None
    pos = None
    path = None
    entry = None
    entries = None

    # load the file from the repository
    if whom[0] == 'source':
      if len(whom) < 2:
        raise TracError('[[Missing argument(s) for citing from source; Usage: BibAdd(source:file@rev)]]')
      elif len(whom) == 2:
        rev = 'latest'
      else:
        rev = whom[2]

      file = whom[1]

      repos = self.env.get_repository()
      bib = repos.get_node(file, rev)
      file = bib.get_content()
      string = file.read()

    # load the file from the wiki attachments
    elif whom[0] == 'attachment':
      if (len(whom) != 2):
        raise TracError('Wrong syntax for environment \'attachment\'; Usage: BibAdd(attachment:file)')

      pos = 'wiki'
      page = None
      file = whom[1]
      path_info = whom[1].split('/',1)
      if len(path_info) == 2:
        page = path_info[0]
        file = path_info[1]
      else:
        page = formatter.req.args.get('page')
        if (page == None):
          page = 'WikiStart'

      bib = Attachment(self.env,pos,page,file)
      file = bib.open()
      string = file.read()

    # use wiki page itself
    elif whom[0] == 'wiki':
      if (len(whom) != 2):
        raise TracError('Wrong syntax for environment \'wiki\'; Usage BibAdd(wiki:page)')
      
      page = WikiPage(self.env,whom[1])
      if page.exists:
        if '{{{' in page.text and '}}}' in page.text:
          tmp = re.compile('{{{|}}}',2).split(page.text)
          string = tmp[1]
        else:
          raise TracError('No code block on page \'' + whom[1] + '\' found.')
      else:
        raise TracError('No wiki page named \'' + whom[1] + '\' found.')
    else:
      raise TracError('Unknown location \''+ whom[0] +'\'')
    try:
        # handle all data as unicode objects
        try:
            u = unicode(string,"utf-8")
        except TypeError:
            u = string
        entries = extract_entries(u)
    except UnicodeDecodeError:
        raise TracError("A UnicodeDecodeError occured while loading the data. Try to save the file in UTF-8 encoding.")
    if entries == None:
      raise TracError('No entries from file \''+ args[0] +'\' loaded.')
    
    bibdb = getattr(formatter, BIBDB,{})
    bibdb.update(entries)
    setattr(formatter,BIBDB,bibdb)

class BibCiteMacro(WikiMacroBase):
  implements(IWikiMacroProvider)

  def render_macro(self, request,name,content):
    return self.expand_macro(request,name,content)
  
  def expand_macro(self,formatter,name,content):

    args, kwargs = parse_args(content, strict=False)

    if len(args) > 1:
      raise TracError('Usage: [[BibCite(BibTexKey)]]')
    elif len(args) < 1:
      raise TracError('Usage: [[BibCite(BibTexKey)]]')
    
    key = args[0];

    bibdb = getattr(formatter, BIBDB,{})
    citelist = getattr(formatter, CITELIST,[])
    
    if key not in citelist:
      citelist.append(key)
      setattr(formatter,CITELIST,citelist)
    
    index = citelist.index(key) + 1
  
    return ''.join(['[', str(tag.a(name='cite_%s' % key)), str(tag.a(href='#%s' % key)('%d' % index)), ']'])

class BibNoCiteMacro(WikiMacroBase):
  implements(IWikiMacroProvider)
  
  def render_macro(self, request,name,content):
    return self.expand_macro(request,name,content)

  def expand_macro(self,formatter,name,content):

    args, kwargs = parse_args(content, strict=False)

    if len(args) > 1:
      raise TracError('Usage: [[BibNoCite(BibTexKey)]]')
    elif len(args) < 1:
      raise TracError('Usage: [[BibNoCite(BibTexKey)]]')
    
    key = args[0];

    bibdb = getattr(formatter, BIBDB,{})
    citelist = getattr(formatter, CITELIST,[])
    
    if key not in citelist:
      citelist.append(key)
      setattr(formatter,CITELIST,citelist)
  
    return


class BibRefMacro(WikiMacroBase):
  implements(IWikiMacroProvider)

  def render_macro(self, request,name,content):
    return self.expand_macro(request,name,content)

  def expand_macro(self,formatter,name,content):
    citelist = getattr(formatter, CITELIST,[])
    bibdb = getattr(formatter, BIBDB,{})

    page = WikiPage(self.env,'BibTex')
    if page.exists:
      if '{{{' in page.text and '}}}' in page.text:
        tmp = re.compile('{{{|}}}',2).split(page.text)
        bibdb.update(extract_entries(tmp[1]))
        setattr(formatter,BIBDB,bibdb)

    str = ''
    for k in citelist:
      if bibdb.has_key(k) == False:
        str +='No entry ' + k + ' found.\n'
    if str != '':
      raise TracError('[[' + str + ']]')

    l = []
    for k in citelist:
      content = []
      for bibkey in BIBTEX_KEYS:
        if bibdb[k].has_key(bibkey):
          content.append(tag.span(Markup(bibdb[k][bibkey] + ', ')))
      if bibdb[k].has_key('url') == False:
        l.append(tag.li(tag.a(name=k), tag.a(href='#cite_%s' % k)('^') ,content))
      else:
        url = bibdb[k]['url']
        l.append(tag.li(tag.a(name=k), tag.a(href='#cite_%s' % k)('^') ,content, tag.br(),tag.a(href=url)(url)))

    ol = tag.ol(*l)
    tags = []
    tags.append(tag.h1(id='References')('References'))
    tags.append(ol)

    return tag.div(id='References')(*tags)
