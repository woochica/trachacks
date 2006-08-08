from trac.core import *

import os

from api import IEnvironmentProvider

class SiblingProviderModule(Component):
    """Provides all environments in the same base folder as this one."""
    
    implements(IEnvironmentProvider)
    
    def get_environments(self):
        base_path, _ = os.path.split(self.env.path.rstrip('/'))
        self.log.debug("SiblingProviderModule: Using base path '%s'"%base_path)
        for path in os.listdir(base_path):
            test_path = os.path.join(base_path, path)
            self.log.debug("SiblingProviderModule: Checking path '%s'"%test_path)
            if test_path != self.env.path and os.path.isdir(test_path) and os.access(os.path.join(test_path,'VERSION'), os.R_OK):
                self.log.debug('SiblingProviderModule: Path good')
                yield test_path
        
    def mutable_environments(self):
        return False
