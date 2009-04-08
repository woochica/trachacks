"""
interfaces for listening to repository changes
and configuration of hooks
"""

from trac.core import Interface

class IEmailHandler(Interface):
    
    def invoke(message):
        """what to do on receiving an email"""
