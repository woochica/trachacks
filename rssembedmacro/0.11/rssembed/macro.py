from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.web.chrome import add_stylesheet, Chrome, ITemplateProvider
from urllib2 import Request, urlopen, URLError, HTTPError
from pkg_resources import resource_filename
from trac.wiki.api import parse_args
import re
import feedparser
import urllib

__author__="simon"
__date__ ="$12/04/2009 7:41:16 PM$"

class RssEmbedMacro(WikiMacroBase):
    """RSS Embedding Macro.

    Will embed any rss feed supported by feedparser
    into the  wiki page in the same manner as the tickets macro.

    Useful for adding output form other trac instances to the wiki.

    Used with a single parameter of the RSS URL.
    """
    
    implements(ITemplateProvider)
    

    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        yield 'rssembed', resource_filename(__name__, 'htdocs')

    def split_at(self, a, index):
        return (a[:index], a[index + 1:])

    def remove_extra_spaces(self, data):
        p = re.compile(r'\s+')
        return p.sub(' ', data)

    def remove_html_tags(self, data):
        p = re.compile(r'<.*?>')
        return p.sub('', data)

    def html_unescape(self, text):
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;',"'")
        text = text.replace('&gt;',">")
        text = text.replace('&lt;',"<")
        return text


    def expand_macro(self, formatter, name, args):
        outputText = ""
        #check arguments
        if (args == None or len(args) == 0):
            return None

        largs, kwargs = parse_args(args)
        

        url = kwargs['url']
        details=kwargs['details']
        

        httpReq = Request(url)
        req = formatter.req
        try:
            response = urlopen(httpReq)
            response.close()
        except HTTPError, e:
            outputText += "HTTP_ERROR("+str(e.code)+")"
        except URLError, e:
            outputText += "Check connectivity"
            
        if outputText != "":
            return "Cannot contact server: "+outputText+"\n ("+url+")"

        urllib.urlretrieve(url, "/tmp/feedData.xml");

        #fetch RSS feed
        feedData = feedparser.parse(url)

        if details != None and details.lower() == "true":
            feedData["showDetails"] = True

        

        #truncate entries to 1024 chars
        for entry in feedData["entries"]:
            if entry.has_key('description'):
                entry.description = self.remove_html_tags(entry.description)
                entry.description = self.html_unescape(entry.description)
                entry.description = self.remove_extra_spaces(entry.description)
                if len(entry.description) > 512:
                    shortEntry = entry.description[:512]
                    shortEntry = shortEntry[:shortEntry.rfind(' ')]+"..."
                    entry.description = shortEntry

        add_stylesheet(req, 'rssembed/css/rssembed.css')
        return Chrome(self.env).render_template(req, 'rssFeed.html', feedData, fragment=True)

