"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
Modified by: Alvaro Iradier <alvaro.iradier@polartech.es>
"""

from trac.core import *

class IWikiPrintFormat(Interface):
    """An extension point for adding output formats to the WikiPrint plugin."""
    
    def wikiprint_formats(self, req):
        """Return an iterable of (format, name)."""
        
    def process_wikiprint(self, req, format, title, subject, top, bottom, right, left, header, toctitle, pages):
        """Process and return the wiki output in the given format."""

