# TracRewrite plugin

from trac.core import *
from trac.web.main import IRequestHandler, dispatch_request
from trac.web.api import RequestDone

import re

config_re = re.compile("""^
                          \s*
                          (?P<delim>\S)      # Opening delim
                          (?P<match>.*?)     # Match RE
                          (?<!\\\)(?P=delim) # Middle delim
                          (?P<rewrite>.*?)   # Rewrite string
                          (?<!\\\)(?P=delim) # End delim
                          \s*
                          (?P<opts>\S*)      # Possible options
                          \s* 
                          $""",re.X)

class RewriteError(TracError):
    """Stub error for dealing with rewrite failures"""

class RewritePlugin(Component):
    """Plugin implementing similar features to mod_rewrite in Apache."""
    
    implements(IRequestHandler)
    
    def __init__(self):
        """Note: I am loading and compiling all regexs here,
        so any changes to the config will require a reload."""
        
        self.rewrites = {}
        # Config format: tag = /match/rewrite/[options]
        # Data format: { tag: [ match, rewrite, options ], ... }
        for k,v in self.config.options('rewrites'):
            md = config_re.match(v)
            if md:
                try:
                    match = re.compile(md.group('match'))
                except re.error:
                    self.log.warn("TracRewrite: Unable to compile pattern '%s'"%md.group(1))
                    continue
                rewrite = md.group('rewrite')
                options = md.group('opts') or 'l'
                self.log.debug("TracRewrite: Loaded rewrite ('%s', '%s', %s')"%( match.pattern, rewrite, options.lower() ) )
                self.rewrites[k.strip()] = ( match, rewrite, options.lower() )
            else:
                self.log.warn("TracRewrite: Unable to parse value '%s'"%v)
                
    # IRequestHandler methods
    def match_request(self, req):
        path = req.path_info
        for k,v in self.rewrites.iteritems():
            md = v[0].match(path)
            if md:
                req.tag = k
                req.md = md
                return True
        return False
        
    def process_request(self, req):
        _, rewrite, options = self.rewrites[req.tag]
        try:
            new_path = req.md.expand(rewrite)
        except re.error:
            raise RewriteError, "Invalid rewrite string given: '%s'"%rewrite
        self.log.debug("TracRewrite: New path is '%s'"%new_path)
        if 'r' in options:
            req.redirect(new_path)
        elif 'p' in options:
            raise RewriteError, "TracRewrite doesn't support proxying yet. Sorry"
        elif 'l' in options:
            dispatch_request(new_path, req, self.env)
            return False # This indicates that a response has already been sent
        else:
            raise RewriteError, "No valid options found in '%s'. Please specify a valid rewrite type."%options
                
