import urllib2
from genshi.builder import tag
from trac.wiki.macros import WikiMacroBase

revison="$Rev$"
url="$URL$"

class DailyLolMacro(WikiMacroBase):
    """Display a picture of a cat with a funny caption.
    Usage:
    {{{
    [[DailyLol]]
    }}}
    """

    def expand_macro(self, formatter, name, content):        

        website = urllib2.urlopen("http://icanhascheezburger.com/")
        website_html = website.read()
        print website_html

        beg_pos = -1
        beg_pos = website_html.find('<img src="', beg_pos+1)
        end_pos = website_html.find('"', beg_pos+10)
        raw_url = website_html[beg_pos+10:end_pos]

        attr = {}
        out = tag.img(src=raw_url, **attr)

        return out
