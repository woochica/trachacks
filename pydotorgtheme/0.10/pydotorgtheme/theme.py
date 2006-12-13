from trac.core import *

from themeengine.api import ThemeBase

__all__ = ['PyDotOrgTheme']

class PyDotOrgTheme(ThemeBase):
    """A theme based on http://www.python.org."""
    
    css = screenshot = True

    header_logo = {
        'src': 'http://www.python.org/images/python-logo.gif',
        'alt': 'homepage',
        'height': '71',
        'link': 'http://www.python.org/',
        'width': '211',
    }
