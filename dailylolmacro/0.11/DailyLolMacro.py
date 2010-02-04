class DailyLolMacro(WikiMacroBase):
    """Display a picture of a cat with a funny caption.
    Usage:
    {{{
    [[DailyLol]]
    }}}
    """

    def expand_macro(self, formatter, name, args):
        import urllib2

        website = urllib2.urlopen("http://www.icanhascheezburger.com")
        website_html = website.read()

        beg_pos = -1
        beg_pos = website_html.find('<img title', beg_pos+1)
        beg_pos = website_html.find('src=', beg_pos)
        end_pos = website_html.find('"', beg_pos+5)
        raw_url = website_html[beg_pos+5:end_pos]

        attr = {}
        result = tag.img(src=raw_url, **attr)

        return result
