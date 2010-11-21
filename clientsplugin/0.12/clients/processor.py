from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem, parse_args
from trac.wiki import wiki_to_html
from trac.wiki.macros import WikiMacroBase
from trac.env import IEnvironmentSetupParticipant
from trac.wiki.parser import WikiParser
from StringIO import StringIO

class ClientWikiProcessor(Component):
  implements(IWikiMacroProvider)
    
  def __init__(self):
    pass
  
  def get_macros(self):
    return ['client']
  
  def get_macro_description(self, name):
    return 'No real formatting but allows for easy extraction of specific text blocks designed to be displayed to the client'
  
  def expand_macro(self, formatter, name, content):
    return '<fieldset class="client"><legend>Comments to Client</legend>%s</fieldset>' % \
           wiki_to_html(content, self.env, formatter.req)


def extract_client_text(text, sep="----\n"):
  buf = StringIO()
  stack = 0
  gotblock = False
  realsep = ''
  for line in text.splitlines():
    if stack:
      realsep = sep
      if line.strip() == WikiParser.ENDBLOCK:
        stack = stack - 1
      if stack:
        buf.write(line + "\n")
        realsep = ''
    if gotblock:
      if line.strip() == '#!client':
        stack = stack + 1
        if stack == 1:
          buf.write(realsep)
      else:
        gotblock = False
    elif line.strip() ==  WikiParser.STARTBLOCK:
      gotblock = True
  return buf.getvalue() 

class TestProcessor(Component):
  implements(IWikiMacroProvider)
    
  def __init__(self):
    pass
  
  def get_macros(self):
    return ['clientx']
  
  def get_macro_description(self, name):
    return 'Just a test'
  
  def expand_macro(self, formatter, name, content):
    db = self.env.get_read_db()
    cursor = db.cursor()
    cursor.execute("SELECT text FROM wiki WHERE name=%s ORDER BY version DESC LIMIT 1", ("WikiStart",))
    try:
      text = extract_client_text(cursor.fetchone()[0])
      return wiki_to_html(text, self.env, formatter.req)
    except:
      return 'B0rken'
