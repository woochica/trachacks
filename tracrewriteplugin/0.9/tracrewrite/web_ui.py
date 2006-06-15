# TracRewrite plugin

from trac.core import *
from trac.web.main import IRequestHandler, dispatch_request
from trac.web.api import RequestDone

import re

config_re = re.compile("""^
                          \s*
                          (?P<match>\S*?)        # Match RE
                          \s+
                          (?P<rewrite>\S*?)      # Rewrite string
                          \s+
                          (?:\[(?P<opts>\S*)\])? # Possible options
                          \s* 
                          $""",re.X)

class RewriteError(TracError):
    """Stub error for dealing with rewrite failures"""

class RewritePlugin(Component):
    """Plugin implementing similar features to mod_rewrite in Apache."""
    
    implements(IRequestHandler)
    
    def __init__(self):
        self.mtime = 0
        self._load_config()
                
    # IRequestHandler methods
    def match_request(self, req):
        self._load_config_if_needed()
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
        elif 'n' in options:
            pass
        elif 'l' in options:
            raise RewriteError, "Internal rewrites don't actually work yet. Check back after 0.10 get finalized a bit more"
            dispatch_request(new_path, req, self.env)
            return False # This indicates that a response has already been sent
        else:
            raise RewriteError, "No valid options found in '%s'. Please specify a valid rewrite type."%options
                

    def _load_config(self):
        """(Re)load config from trac.ini"""        
        self.rewrites = []
        # Config format: tag = /match/rewrite/[options]
        # Data format: { tag: [ match, rewrite, options ], ... }
        for k,v in self.config.options('rewrites'):
            md = config_re.match(v)
            if md:
                tag = k.strip()
                try:
                    match = re.compile(md.group('match'))
                except re.error:
                    self.log.warn("TracRewrite: Unable to compile pattern '%s'"%md.group('match'))
                    continue
                rewrite = md.group('rewrite')
                opt_string = md.group('opts') or 'r'
                options = []
                for opt in opt_string.split(','):
                    n = opt.split('=')
                    if len(n) == 1:
                        n = (n, None)
                    options.append(n[0:2])
                self.log.debug("TracRewrite: Loaded rewrite ('%s', '%s', %s')"%( match.pattern, rewrite, options ) )
                self.rewrites.append( (tag, match, rewrite, options) )
            else:
                self.log.warn("TracRewrite: Unable to parse value '%s'"%v)
        self.rewrites.sort(lambda a,b: cmp(a[0],b[0]))
        
        # Generate tag location cache
        i = 0
        self.tag_index = {}
        for t,_,_,_ in self.rewrites:
            self.tag_index[t] = i
            i += 1
            
    def _load_config_if_needed(self):
        """Reload the config only if needed."""
        config_mtime = max(self.config._lastmtime,self.config._lastsitemtime)
        if self.mtime < config_mtime:
            self.log.info('TracRewrite: Config mtime is newer than ours; reloading config.')
            self._load_config()
            self.mtime = config_mtime
