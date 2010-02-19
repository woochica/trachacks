# -*- coding: utf-8 -*-

from trac.core import *

from themeengine.api import ThemeBase

class LightGreenTheme(ThemeBase):
    """A light theme for Trac with a discrete green and blue color scheme."""

    htdocs = css = screenshot = True
    
