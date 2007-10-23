from trac.config import Option

# Compatibility hack to make this code work with older 0.11 revisions
try:
    from trac.env import open_environment as _open_environment
    def open_environment(x): return _open_environment(x,True)
except:
    from trac.web.main import _open_environment as open_environment

class EnvironmentOption(Option):
    """Interpret an option as an environment path."""
    
    def accessor(self, *args, **kwords):
        val = super(EnvironmentOption,self).accessor(*args, **kwords)
        assert val, 'You must configure a valid Trac environment path for [%s] %s'%(self.section, self.name)
        return open_environment(val)
