# Created by Jonatan Magnusson, 2008
# Copyright (C) 2008 CM Teknik AB. All rights reserved.

from trac.core import *
from themeengine.api import ThemeBase

class CMTeknikTheme (ThemeBase):
    """A theme for Trac based on http://www.cmteknik.se"""
    template = htdocs = css = True


