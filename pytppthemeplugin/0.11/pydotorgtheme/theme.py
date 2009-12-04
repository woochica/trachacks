# Created by Noah Kantrowitz on 2007-07-16.
# Modified by Olemis Lang on 2009-04-12.
# Copyright (c) 2009 Noah Kantrowitz, Olemis Lang. All rights reserved.

from trac.core import *

from themeengine.api import ThemeBase

class PyTppTheme(ThemeBase):
    """Trac theme based on python.org and The Python Papers."""

    template = htdocs = css = screenshot = True
    
