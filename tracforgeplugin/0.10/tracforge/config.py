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
    
    def __init__(self, section, sep=',', keep_empty=True, doc=''):
        DictOption.__init__(self, section, doc)
        self.sep = sep
        self.keep_empty = keep_empty
        
    def accessor(self, section):
        ret = {}
        for name in section:
            ret[name] = section.getlist(name,sep=self.sep,keep_empty=self.keep_empty)
        return ret
