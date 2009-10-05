"""
interfaces for listening to repository changes
and configuration of hooks
"""

from trac.core import Interface

class IEmailHandler(Interface):
    
    def match(message):
        """
        whether this handler can be used on this message
        """

    def invoke(message, warnings):
        """
        what to do on receiving an email;
        returns the message if it is availble to other 
        IEmailHandler plugins or None
        if the message is consumed
        warnings is a list of warnings to append to
        """
