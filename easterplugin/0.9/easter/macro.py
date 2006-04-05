# vim: expandtab tabstop=4

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.web.chrome import ITemplateProvider
from StringIO import StringIO
import os, re, inspect, datetime, random

try:
    from dateutil.easter import easter
except ImportError:
    from _easter import easter

__all__ = ['EasterMacro']

class EasterMacro(Component):
    """
    A simple macro to tell you when Easter is.
    """
    
    implements(IWikiMacroProvider, ITemplateProvider)
    
    # IWikiMacroProvider methods
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
            
        output = str(easter(year, method))
        
        def random_egg():
            return "<img src='%s/egg_0%s.gif' />" % (self.env.href.chrome('easter','img'),random.randint(1,4))
            
        return random_egg() + output + random_egg()

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('easter', resource_filename(__name__, 'htdocs'))]
