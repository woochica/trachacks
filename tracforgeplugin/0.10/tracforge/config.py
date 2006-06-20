# New config type
from trac.core import *
from trac.config import *

__all__ = ['DictOption','ListDictOption']

class DictOption(Option):
    """A new config type where a whole section is shown as a dict."""
    
    def __init__(self, section, doc=''):
        """Note: Unlike with the other options, the default is always {}."""
        self.section = section
        self.__doc__ = doc
        self.registry[(self.section, '*')] = self
        
    def __get__(self, instance, owner):
        if instance is None:
            return self
        config = getattr(instance, 'config', None)
        if config and isinstance(config, Configuration):
            section = config[self.section]
            value = self.accessor(section)
            return value
        return None

    def accessor(self, section):
        return dict(section.options())
        
    def __repr__(self):
        return '<%s [%s]>'%(self.__class__.__name__,self.section)

class ListDictOption(DictOption):
    """Pretty self explanatory."""
    
    def __init__(self, section, sep=',', doc=''):
        DictOption.__init__(self, section, doc)
        self.sep = sep
        
    def accessor(self, section):
        opts = section.options()
        return dict(map(lambda x: (x[0],x[1].split(self.sep)), list(opts)))
