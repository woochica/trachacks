"""
enhancements to trac's configuration
see http://trac.edgewall.org/browser/trunk/trac/config.py
"""

from trac.config import Configuration
from trac.config import ConfigurationError
from trac.config import Option
from trac.config import Section

def getfloat(self, name, default=''):
    value = self.get(name, default)
    if not value:
        return 0.
    try:
        return float(value)
    except ValueError:
        raise ConfigurationError('[%(section)s] %(entry)s: expected float, got %(value)s' % dict(section=self.name, entry=name, value=repr(value)))

Section.getfloat = getfloat

def config_getfloat(self, section, name, default=''):
    return self[section].getfloat(name, default)

Configuration.getfloat = config_getfloat

class FloatOption(Option):
    accessor = Section.getfloat
