# MacroPost Interfaces
# Copyright 2006 Noah Kantrowitz
from trac.core import *

class IMacroPoster(Interface):
    """An interface to allow a macro to POST."""
    
    def match_macro_post(req):
        """You have two options with this, either return True or False 
        indicating if you should process the request, or for simplicity
        just return a string. If you do the latter, it will be treated 
        as `rv in req.args.keys()`. This is optional, if no handlers
        claim a non-WikiModule POST, any macro providers implmenting only
        `process_macro_post` will be passed the req."""
        
    def process_macro_post(req):
        """Do stuff with the request."""
