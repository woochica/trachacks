from genshi.builder import tag
from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import format_to_html

class FoldMacro(WikiMacroBase):
    """Expands to a foldable section.
      
      The `title` Wiki processor parameter is the header.
      The Wiki processor content is the folded wiki text.
      """

    def expand_macro(self, formatter, name, content, args):
        html_title = tag.h1(args.get('title', 'Use {{{#!Fold title="Your title"}}}'), class_="foldable")
        html_content = format_to_html(self.env, formatter.context, content)
        return tag.div(
                  tag(html_title,
                      tag.div(html_content)))
