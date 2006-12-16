from trac.core import *

from themeengine.api import ThemeBase

__all__ = ['IntraBlogTheme']

class IntraBlogTheme(ThemeBase):
    """A theme based off the Intra Blog template at templateworld.com"""
    
    header = footer = css = htdocs = True
