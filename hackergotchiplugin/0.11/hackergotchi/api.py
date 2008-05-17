# Created by Noah Kantrowitz on 2008-05-16.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.

from trac.core import *

class IHackergotchiProvider(Interface):
    """An extension-point interface for exposing hackergotchi providers."""
    
    def get_hackergotchi(href, user, name, email):
        """Return an href to an image corresponding the user information
        given.
        
        :param href: An Href object for the current Trac.
        :param user: The username or 'anonymous'
        :param name: The user's full name or None
        :param email: The user's email address or None
        """
