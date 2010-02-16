# Created by Jonatan Magnusson, 2008
# Copyright (C) 2008 CM Teknik AB. All rights reserved.

from trac.core import *
from themeengine.api import ThemeBase

class LittleMaryTheme (ThemeBase):
    """A theme for Trac"""
    template = htdocs = css = True


