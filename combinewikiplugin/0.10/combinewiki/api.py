from trac.core import *

class ICombineWikiFormat(Interface):
    """An extension point for adding output formats to the CombineWiki plugin."""
    
    def combinewiki_formats(self, req):
        """Return an iterable of (format, name)."""
        
    def process_combinewiki(self, req, format, title, pages):
        """Process and return the combined output in the given format."""

