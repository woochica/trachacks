from trac.core import *
from themeengine.api import ThemeBase

__all__ = ['DefaultTheme']

class DefaultTheme(ThemeBase):
    """Trac default theme"""
    
    htdocs = screenshot = True
