from trac.config import Option
from trac.web.main import _open_environment

class EnvironmentOption(Option):
    """Interpret an option as an environment path."""
    
    def accessor(self, *args, **kwords):
        val = super(EnvironmentOption,self).accessor(*args, **kwords)
        assert val, 'You must configure a valid Trac environment path for [%s] %s'%(self.section, self.name)
        return _open_environment(val)
