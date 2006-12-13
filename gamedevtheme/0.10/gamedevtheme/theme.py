from trac.core import *

from themeengine.api import ThemeBase

__all__ = ['GamedevTheme']

class GamedevTheme(ThemeBase):
    """A theme based on the RPI game development club. See http://gamedev.union.rpi.edu."""
    
    css = htdocs = screenshot = True
