import re
import sys
import os
from trac.config import default_dir
from StringIO import StringIO
from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.wiki.macros import ImageMacro
from trac.util.html import escape, html, Markup

class ImageListMacro(WikiMacroBase):
    """
    Displays a list of images available from the project htdocs directory
    Example:
    {{.{
    [[ImageList]]
    }}.}
    """
    def __init__(self):
        self.env_htdocs = os.path.join(self.env.path, 'htdocs')

    def render_macro(self, req, name, content):
        found = []
        output = {}
        imgMacro = ImageMacro(self.env)

        for path in (self.env_htdocs,):
            if not os.path.exists(path):
                continue
            for filename in [filename for filename in os.listdir(path)
                             if filename.lower().endswith('.png')
                             or filename.lower().endswith('.gif')
                             or filename.lower().endswith('.jpg')]:
                found.append(filename)
        for item in found:
            output['Use: [[Image(htdocs:' + item + ')]]'] = imgMacro.render_macro(req, 'Image', 'htdocs:' + item)

        return html.TABLE(class_='wiki')(
                  html.TBODY([html.TR(html.TD(html.TT(output[key])),
                                      html.TD(key))
                              for key in sorted(output.keys())]))