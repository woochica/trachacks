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
        
        self.rewrites = []
        # Config format: tag = /match/rewrite/[options]
        # Data format: { tag: [ match, rewrite, options ], ... }
        for k,v in self.config.options('rewrites'):
            md = config_re.match(v)
            if md:
                tag = int(k.strip())
                try:
                    delim = md.group('delim')
                    match_pat = re.sub('\\'+delim,delim,md.group('match'))
                    match = re.compile(match_pat)                                        
                except re.error:
                    self.log.warn("TracRewrite: Unable to compile pattern '%s'"%md.group('match'))
                    continue
                rewrite = md.group('rewrite')
                options = md.group('opts') or 'r'
                self.log.debug("TracRewrite: Loaded rewrite ('%s', '%s', %s')"%( match.pattern, rewrite, options.lower() ) )
                self.rewrites.append( (tag, match, rewrite, options.lower()) )
            else:
                self.log.warn("TracRewrite: Unable to parse value '%s'"%v)
        self.rewrites.sort(lambda a,b: cmp(a[0],b[0]))
        
        # Generate tag location cache
        i = 0
        self.tag_index = {}
        for t,_,_,_ in self.rewrites:
            self.tag_index[t] = i
            i += 1
                
    # IRequestHandler methods
    def match_request(self, req):
        path = req.path_info
        for t,m,_,_ in self.rewrites:
            md = m.match(path)
            if md:
                req.tag = t
                req.md = md
                return True
        return False
        
    def process_request(self, req):
        _, _, rewrite, options = self.rewrites[self.tag_index[req.tag]]
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
            raise RewriteError, "Internal rewrites don't actually work yet. Check back after 0.10 get finalized a bit more"
            dispatch_request(new_path, req, self.env)
            return False # This indicates that a response has already been sent
        else:
            raise RewriteError, "No valid options found in '%s'. Please specify a valid rewrite type."%options
                
