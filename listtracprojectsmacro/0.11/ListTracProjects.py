# -*- coding: utf-8 -*-
# List all Trac Plugins in a parent directory.

from trac.wiki.macros import WikiMacroBase
import os

class ListTracProjectsMacro(WikiMacroBase):
    '''
    Trac 0.11 port of the ListTracProjects Macro
    '''

    def render_macro(self, req, name, content):
      DIR = '/srv/trac/teams-example'
      str = ''
      i = 0

      for f in os.listdir(DIR):
         if (i==0):
            str = '<a href="/teams-example/' + f + '" target="_new">' + f + '</a>'
            i = i + 1
         else:
            str = str + ' :: ' + '<a href="/teams-example/' + f + '" target="_new">' + f + '</a>'
      return str + '<br>'