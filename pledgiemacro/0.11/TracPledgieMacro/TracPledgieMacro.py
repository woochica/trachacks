""" License: GPLv3
    Author: Stephan
"""

from trac.core import *
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from StringIO import StringIO
from trac.util.html import escape,Markup
from genshi.builder import tag

class PledgieMacro(WikiMacroBase):
    """ Displays the pledgie badge
    """

    def expand_macro(self, formatter, name, content):
	content = content or ''
	args = content.split(',')

        # HTML arguments used in Pledgie URL (future maybe...)
        hargs = {
            'key'    : self.env.config.get('pledgie', 'campaign_id', None)
            }

        if not content:
            raise TracError("No campaign id given! The campaign id can be found in the pledgie url, e.g. http://pledgie.com/campaigns/ID\n")

        return tag.a(
                    tag.img(
                          src    = "http://www.pledgie.com/campaigns/" + args[0] + ".png"
#                        title  = Markup.escape(title, quotes=True),
#                        alt    = Markup.escape(alt,   quotes=True),
                    ),
                    class_ = "pledgiemacro",
                    href   = "http://www.pledgie.com/campaigns/" + args[0]
               )
