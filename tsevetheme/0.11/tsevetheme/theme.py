# Created by Carlos Jenkins (Havok), 2009
# http://www.cjenkins.net/
# Copyleft (C) 2009 Carlos Jenkins. Some rights reserved.

from trac.core import *
from themeengine.api import ThemeBase

class TseveTheme(ThemeBase):
	"""Tseve Minimalist Theme for Trac"""
	template = htdocs = css = True
