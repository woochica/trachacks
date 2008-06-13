# Created by Danial Pearce

from trac.core import *
from trac.config import Option

from themeengine.api import ThemeBase

class SkittlishTheme(ThemeBase):
  """A port of the mephisto theme, Skittlish, created by evil.che.lu."""

  theme_color = Option('theme', 'skittlish_color', default='blue', doc='The color to use.')

  color = template = htdocs = css = True

  def get_theme_info(self, name):
    info = super(SkittlishTheme, self).get_theme_info(name)

    self._set_info(info, 'color', self.theme_color)

    return info
