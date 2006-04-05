# vim: expandtab tabstop=4

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from StringIO import StringIO
import os, re, inspect, datetime

try:
    from dateutil.easter import easter
except ImportError:
    from _easter import easter

__all__ = ['EasterMacro']

class EasterMacro(Component):
    """
    A simple macro to tell you when Easter is.
    """
    
    implements(IWikiMacroProvider)
    
    def get_macros(self):
        yield 'Easter'
        
    def get_macro_description(self, name):
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, args):
        if args == None: args = ''
        args = [x.strip() for x in args.split(',')]
        
        year = datetime.date.today().year
        method = 3
        if len(args) >= 1 and args[0] != '':
            year = int(args[0])
        if len(args) >= 2:
            method = int(args[1])
        
        self.log.debug('Calling easter(%s,%s)'%(year,method))    
        return str(easter(year,method))
