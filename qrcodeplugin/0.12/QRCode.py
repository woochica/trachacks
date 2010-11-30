import urllib2
from genshi.builder import tag
from trac.wiki.macros import WikiMacroBase
from trac.resource import get_resource_url

revison="$Rev$"
url="$URL$"

class QRCodeMacro(WikiMacroBase):
    """Display a QR Code for the current wiki page URL
    Usage:
    {{{
    [[QRCode]]
    }}}
    """

    def expand_macro(self, formatter, name, content):        
        
        qrc_url = 'http://chart.apis.google.com/chart?cht=qr&chs=120x120&chl='
        req_url = get_resource_url(self.env, formatter.context.resource, formatter.req.abs_href)

        out = '<a href="' + req_url + '"><img src="' + qrc_url + req_url + '" border="0"></a>'

        return out
