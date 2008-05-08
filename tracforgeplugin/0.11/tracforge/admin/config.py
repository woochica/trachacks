# Created by Noah Kantrowitz
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
from trac.config import Option
from trac.env import open_environment

class EnvironmentOption(Option):
    """Interpret an option as an environment path."""
    
    def accessor(self, *args, **kwords):
        val = super(EnvironmentOption,self).accessor(*args, **kwords)
        assert val, 'You must configure a valid Trac environment path for [%s] %s'%(self.section, self.name)
        return open_environment(val, use_cache=True)
