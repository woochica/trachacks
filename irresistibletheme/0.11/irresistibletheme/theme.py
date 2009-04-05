# Created by Noah Kantrowitz on 2009-04-04.
# Copyright (c) 2009 Noah Kantrowitz. All rights reserved.

from trac.core import *

from themeengine.api import ThemeBase

class IrresistibleTheme(ThemeBase):
    """A theme for Trac based on http://www.woothemes.com/2009/02/irresistible/."""

    template = htdocs = css  = True
    disable_trac_css = True
    
