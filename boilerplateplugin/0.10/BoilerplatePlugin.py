#!/usr/local/bin/python
#
# Copyright (c) 2007, Danny MacMillan
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * The name of Danny MacMillan may not be used to endorse or promote
#     products derived from this software without specific prior written
#     permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# INSTALLATION
#
# Copy the BoilerplatePlugin.py file to your trac plugins directory
# (/usr/share/trac/plugins on my machine).
#
# No other configuration is neccessary. 

import re
from trac.core import *
from trac.wiki.api import IWikiChangeListener, IWikiMacroProvider
from trac.wiki.model import WikiPage
from trac.util import Markup, escape, sorted, reversed
from StringIO import StringIO

class BoilerplatePlugin(Component):
  """Automatically generates Wiki pages based on boilerplate Wiki markup with
  parameter placeholders and tables describing pages to create with argument
  lists on special 'boilerplate' Wiki pages.
  
  Boilerplate Wiki markup is defined by placing it between special
  `[[BoilerplateStart]]` and `[[BoilerplateEnd]]` macros.  Within such a
  boilerplate section, placeholders for parameter replacement can be described
  by `{{`''n''`}}`, where ''n'' is an integer greater than or equal to zero.
  
  Boilerplate Wiki markup is hidden when the boilerplate page is rendered.
  
  The pages to generate are defined by declaring how they should be generated
  in a Wiki table on the same page as the boilerplate Wiki markup.  The first
  column must contain either the name of, or a MoinMoin-style free link to, the
  page to be generated.  Subsequent columns contain text to be inserted into
  the Wiki page as described by the placeholders for parameter replacement
  in the boilerplate Wiki markup.  `{{1}}` will be replaced by the contents of
  the first column after the target page column, `{{2}}` will be replaced by
  the contents of the second column after the target page column, etc.  `{{0}}`
  will be replaced by the name of the page extracted from the first column
  '''without''' the link markup if present.  Table rows whose contents are bold
  are ignored, to allow headers.
  
  When a Wiki page with boilerplate Wiki markup is created or its content is
  changed, the plugin searches the page for table rows.  It takes the
  boilerplate Wiki markup, performs parameter replacements as described above,
  and saves the resulting text into a new or existing Wiki page whose name is
  extracted from the first column.  If the page already exists and the
  desired text is identical to the current page contents, the page is not saved.
  
  Aside from the boilerplate markup and the descriptive table, the boilerplate
  page itself can have any other arbitrary Wiki markup, which allows the
  boilerplate page to itself have documentary value.  This is also the reason
  the boilerplate markup is not shown when the boilerplate page is rendered.
  
  Example Wiki markup for a boilerplate page follows:
  
  {{{
  = Noble Gases =
  
  This table describes the attributes of the noble, or inert, gases.
  
  ||'''Element Symbol''' ||'''Element Name''' ||'''Atomic Number''' ||
  ||["He"]               ||Helium             ||2                   ||
  ||["Ne"]               ||Neon               ||10                  ||
  ||["Ar"]               ||Argon              ||18                  ||
  ||["Kr"]               ||Krypton            ||36                  ||
  ||["Xe"]               ||Xenon              ||54                  ||
  ||["Rn"]               ||Radon              ||86                  ||
  ||["Uuo"]              ||Ununoctium         ||118                 ||
  
  [[BoilerplateStart]]
  = {{0}} =
  
  The element {{1}} is a noble gas with an atomic number of {{2}}.  Like all
  noble gases, it has a full complement of electrons in its outer valence.
  [[BoilerplateEnd]]
  }}}
  
  This would result in seven pages being generated, the first of which would
  look like this:
  
  {{{
  = He =
  
  The element Helium is a noble gas with an atomic number of 2.  Like all
  noble gases, it has a full complement of electrons in its outer valence.
  }}}
  
  ''Many thanks to Alec Thomas, whose AcronymsPlugin provided the instruction I
  needed to author this plugin.''
  """

  implements(IWikiChangeListener,IWikiMacroProvider)

  def __init__(self):
    self.boilerplate_start_re = re.compile( r"\[\[BoilerplateStart(\(\))?\]\]" )
    self.boilerplate_end_re = re.compile( r"\[\[BoilerplateEnd(\(\))?\]\]" )
    self.extractpagename_re = re.compile( r'\["([^"]+)"]' )

  def _process_page(self, page, author = None, comment = None, ipnr = None):
    
    if self.boilerplate_start_re.search( page.text ) != None:
      
      # If the audit info isn't available, grab it from the boilerplate page.
      if author == None or comment == None:
        page = WikiPage( self.env, page.name )
      if author == None:
        author = page.author
      if comment == None:
        comment = page.comment
      if ipnr == None:
        ipnr = '127.0.0.1' # I don't know what else to do here.
      
      # Extract the boilerplate text and the wanted pages.
      buf = StringIO()
      page_list = {}
      inboilerplate = False
      for line in page.text.splitlines():
        if inboilerplate:
          if self.boilerplate_end_re.search( line ) != None:
            inboilerplate = False
          else:
            buf.write( line )
            buf.write( '\n' )
        else:
          if self.boilerplate_start_re.search( line ) != None:
            inboilerplate = True
          else:
            if line.startswith('||') and line.endswith('||') and line[3] != "'":
              try:
                descriptor = ([i.strip() for i in line.strip('||').split('||')])
                name = descriptor[0]
                arguments = descriptor[1:]
                m = self.extractpagename_re.search( name )
                if m != None:
                  name = m.string[m.start(1):m.end(1)]
                  self.env.log.warning("extracted name = " + name )
                page_list[ name ] = arguments
              except Exception, e:
                self.env.log.warning("Invalid page line: %s (%s)", line, e)
      
      # Generate the derived pages as instructed.
      page_names = page_list.keys()
      page_names.sort()
      for name in page_names:
        text = buf.getvalue()
        args = page_list[ name ]
        text = text.replace( '{{0}}', name )
        i = 0
        for arg in args:
          text = text.replace('{{%d}}' % (i+1), args[i])
          i += 1
        newpage = WikiPage( self.env, name )
        if newpage.text != text:
          newpage.text = text
          newpage.save( author, comment, ipnr )

  # IWikiChangeListener methods
  
  def wiki_page_added(self, page):
    self._process_page(page)

  def wiki_page_changed(self, page, version, t, comment, author, ipnr):
    self._process_page(page,author,comment,ipnr)

  def wiki_page_deleted(self, page):
    pass

  def wiki_page_version_deleted(self, page):
    self._process_page(page)

  # IWikiMacroProvider methods.
  
  def get_macros(self):
    """Yield the names of the macros supplied by this plugin."""
    yield 'BoilerplateStart'
    yield 'BoilerplateEnd'

  def get_macro_description(self, name):
    """Get the description of the specified macro."""
    if name == 'BoilerplateStart':
      return 'Macro to flag the beginning of the boilerplate text.'
    elif name == 'BoilerplateEnd':
      return 'Macro to flag the end of the boilerplate text.'
    else:
      raise NotImplementedError

  def render_macro(self, req, name, content):
    """Render the specified macro."""
    if name == 'BoilerplateStart':
      return "<div style='display:none;'>"
    elif name == 'BoilerplateEnd':
      return '</div>'
    else:
      raise NotImplementedError
