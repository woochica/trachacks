from trac.core import *

from themeengine.api import ThemeBase

__all__ = ['ConsultantTheme']

class ConsultantTheme(ThemeBase):
    """A theme based off the G-Consultant template at templateworld.com"""
    
    header = footer = css = htdocs = screenshot = True
