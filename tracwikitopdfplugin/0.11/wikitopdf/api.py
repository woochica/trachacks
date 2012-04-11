"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

from trac.core import Interface

class IWikiToPdfFormat(Interface):
    """An extension point for adding output formats to the WikiToPdf plugin."""
    
    def wikitopdf_formats(self, req):
        """Return an iterable of (format, name)."""
        
    def process_wikitopdf(self, req, format, title, subject, top, bottom, right, left, header, toctitle, pages):
        """Process and return the wiki output in the given format."""

