"""
display SVN URLs in trac's respository browser
"""

from genshi.builder import tag 
from genshi.filters.transform import StreamBuffer
from genshi.filters.transform import Transformer
from genshi.input import TEXT

from trac.core import *
from trac.config import Option
from trac.web import ITemplateStreamFilter

class SVNURLs(Component):
    implements(ITemplateStreamFilter)

    ### class data
    
    svn_base_url = Option('svn', 'repository_url',
                          doc="base URL of svn repository")
    link_text = Option('svnurls', 'link_text', default='[svn]',
                         doc="text display for svn url links")

    link_title = "URL of SVN location"
    element_class = "name" # class of the div after which to insert the svn url

    class GenerateSVNUrl(object):
        """class to generate svn urls from table data"""

        def __init__(self, buffer, svn_base_url, link_text, browser_link):
            self.buffer = buffer
            self.svn_base_url = svn_base_url.rstrip('/')
            self.link_text = link_text
            self.browser_link = browser_link.rsplit('?', 1)[0]

        def __iter__(self):
            link = self.buffer.events[0][1][1].get('href').split(self.browser_link)[-1]
            link = self.svn_base_url + link.rsplit('?', 1)[0]
            return iter(tag.td(tag.a(self.link_text, href=link, title=SVNURLs.link_title)))

    
    def url(self, path):
        return u'/'.join((self.svn_base_url.rstrip(u'/'), path.lstrip(u'/')))

    ### methods for handling different views
    ### these should return the stream

    def browser(self, req, stream, data):

        if not data.has_key('path'):
            # this probably means that there is an upstream error
            return stream

        # mark up the title (disabled)
        # stream |= Transformer('//title/text()').substitute('/', data['svn_base_url'] + '/')

        # provide a link to the svn repository
        stream |= Transformer("//div[@id='content']/h1").after(tag.a(self.link_text, href=self.url(data['path']), title=self.link_title))

        # if a directory, provide links to the children files
        if data['dir']:
            offset = 2 # table header, index of 0 (python) versus 1 (xpath)
            if data['path'] != '/':                
                offset += 1 # parent directory row

            xpath_prefix = "//table[@id='dirlist']"
            # add the table header
            xpath = xpath_prefix + "//th[contains(@class, '%s')]" % self.element_class
            stream |= Transformer(xpath).after(tag.th('URL', **{'class': "url"}))

            if 'up' in data['chrome']['links']:
                stream |= Transformer(xpath_prefix + "//td[@colspan='5']").attr('colspan', None)

            # add table cells
            stream = self.dir_entries(req, stream, data, xpath_prefix)
        return stream

    def dir_entries(self, req, stream, data, xpath_prefix=''):
        # add table cells
        b = StreamBuffer()
        xpath = "//td[@class='%s']"
        stream |= Transformer(xpath_prefix + (xpath % 'name') + "/a/@href").copy(b).end().select(xpath_prefix + (xpath % self.element_class)).after(self.GenerateSVNUrl(b, self.svn_base_url, self.link_text, data['path_links'][0]['href']))
        return stream

    def svnlog(self, req, stream, data):

        if not data.has_key('path'):
            # this probably means that there is an upstream error
            return stream

        # provide a link to the svn repository
        stream |= Transformer("//div[@id='content']/h1").after(tag.a(self.link_text, href=self.url(data['path']), title=self.link_title))
        
        return stream

    def changelog(self, req, stream, data):
        changes = data['changes']
        url = self.url(data['location'])
        stream |= Transformer("//dt[@class='property files']").before(tag.dt('URL:', **{'class': "property url"}) + tag.dd(tag.a(url, **{'class': "url", 'href': url, 'title': self.link_title})))

        # make the header link to the canonical location if just at '/changeset'
        if req.path_info.strip('/') == 'changeset':
            stream |= Transformer("//h1").wrap(tag.a(None, href=req.href('changeset', data['new_rev'])))

        return stream

    # method for ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """

        svn_base_url = self.svn_base_url.rstrip('/')

        handlers = { 'browser.html': self.browser,
                     'dir_entries.html': self.dir_entries,
                     'revisionlog.html': self.svnlog,
                     'changeset.html': self.changelog,
                    }

        if svn_base_url:
            handler = handlers.get(filename, lambda req, stream, data: stream)
            return handler(req, stream, data)
    
        return stream

