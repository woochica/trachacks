from trac.core import *

class IWikitoPDFFormat(Interface):
    """An extension point for adding output formats to the WikitoPDF plugin."""
    
    def wikitopdf_formats(self, req):
        """Return an iterable of (format, name)."""
        
    def process_wikitopdf(self, req, format, title, subject, top, bottom, right, left, header, toctitle, pages):
        """Process and return the wiki output in the given format."""

