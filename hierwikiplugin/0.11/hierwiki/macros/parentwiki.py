# Macros for the HierWiki plugin

from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem

from StringIO import StringIO
import re, string, inspect

class ParentWikiMacro(Component):
    """
    Inserts a link to the "parent" wiki entry.  
    
    This only applies to wikis that have a "/" in their name indicating heirarchy.  
    
    e.g. an entry named Java/Introduction will have a parent of Java.  All other wiki entries have a parent of WikiStart.
    """

    # TODO: Everything until render_macro can be removed once switched to be based on WikiMacroBase
    implements(IWikiMacroProvider)
    
    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        name = self.__class__.__name__
        if name.endswith('Macro'):
            name = name[:-5]
        yield name
        
    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return inspect.getdoc(self.__class__)
        
    def expand_macro(self, formatter, name, args):
        db = self.env.get_db_cnx()    
        cursor = db.cursor()
            
        buf = StringIO()    
        
        prefix = None    
        if args:        
            prefix = args.replace('\'', '\'\'')    
        else: 
            prefix = formatter.resource.id + '/'    
            
        parent = 'WikiStart'    
        
        m = re.search("(\S+)/(\S+)$", prefix)    
        if m:     
            parent = m.group(1)    
            
        buf.write('<a href="%s">' % self.env.href.wiki(parent))    
        buf.write(parent)    
        buf.write('</a>\n')    
        return buf.getvalue()
