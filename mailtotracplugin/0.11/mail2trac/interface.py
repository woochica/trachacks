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

    def invoke(message):
        """
        what to do on receiving an email;
        returns the message if it is availble to other 
        IEmailHandler plugins or None
        if the message is consumed
        """

    def order():
        """
        what order to process the IEmailHandler in.
        higher order == higher precedence
        """
