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
#from trac.versioncontrol.api import NoSuchChangeset, RepositoryManager

class SVNMULTIURLs(Component):
    """
    [components]
    svnmultiurls.* = enabled
    [svnmultiurl]
    repository_root_url = /svn
    or
    [svnmultiurl]
    repository_root_url = http://host/svn
    The name of the repositories must be exactly the same like the directory
    name of the repository directory !
    Delete also the deprecated pramater "repository_dir" from trac.ini !
    Optionally, you may also add an entry to this section controlling what
    text is displayed:
    [svnmultiurl]
    link_text = [svn]
    """
    implements(ITemplateStreamFilter)

    ### class data
    
    svn_base_url = Option('svnmultiurls', 'repository_root_url', default='/svn', doc="root URL of svn repositories")
    link_text = Option('svnmultiurls', 'link_text', default='[svn]', doc="text display for svn url links")

    link_title = "URL of SVN location"
    element_class = "name" # class of the div after which to insert the svn url
    header_element_class = "pathentry first" # class of the div after which to insert the svn url

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
            return iter(tag.td(tag.a(self.link_text, href=link, title=SVNMULTIURLs.link_title)))

    
    def index(self, path):
        return u'/'.join((self.svn_base_url.rstrip(u'/'), path.lstrip(u'/')))

    ### methods for handling different views
    ### these should return the stream

    def browser(self, req, stream, data):

        if not data.has_key('path'):
            # this probably means that there is an upstream error
            return stream

        # mark up the title (disabled)
        #stream |= Transformer('//title/text()').substitute('/', data['svn_base_url'] + '/')

        # provide a link to the svn repository
        #stream |= Transformer("//div[@id='content']/h1").after(tag.a(self.link_text, href=self.url(data['path']), title=self.link_title))

        # if a directory, provide links to the children files
        if data['dir']:
            offset = 2 # table header, index of 0 (python) versus 1 (xpath)
            if data['path'] != '/':                
                offset += 1 # parent directory row

            xpath_prefix = "//table[@id='dirlist']"
            # add the table header
            xpath = xpath_prefix + "//th[contains(@class, '%s')]" % self.element_class
            stream |= Transformer(xpath).after(tag.th('Url', **{'class': "url"}))

            if 'up' in data['chrome']['links']:
                stream |= Transformer(xpath_prefix + "//td[@colspan='5']").attr('colspan', None)

            # add table cells
            stream = self.dir_entries(req, stream, data, xpath_prefix)

        # Repository Index
	xpath_prefix = "//table[@id='repoindex']"
        # add the table header
        xpath = xpath_prefix + "//th[contains(@class, '%s')]" % self.element_class
        stream |= Transformer(xpath).after(tag.th('Url', **{'class': "url"}))
	
	if 'up' in data['chrome']['links']:
            stream |= Transformer(xpath_prefix + "//td[@colspan='5']").attr('colspan', None)

        # add table cells
        stream = self.dir_entries(req, stream, data, xpath_prefix)


        # MAIN HEADER
	xpath_prefix = "//h1"
        # add the table header
        xpath = xpath_prefix + "//a[contains(@class, '%s')]" % self.header_element_class
        #mainlink = data['path']
        # Cut first from last path_links element
	firstlink = data['path_links'][0]['href'].rsplit('?', 1)[0]
        mainlink = data['path_links'][-1]['href'].split(firstlink)[-1]
        mainlink = self.svn_base_url + mainlink.rsplit('?', 1)[0]
        stream |= Transformer(xpath).after(tag.a(self.link_text, href=mainlink, title=SVNMULTIURLs.link_title))

        #for dat in data:
        #    self.log.debug('data: %s : %s',dat,data[dat])
	#self.log.debug('data: 0 : %s',data['path_links'][0]['href'])
	#self.log.debug('data: 1 : %s',data['path_links'][-1]['href'])
	

        return stream

    def dir_entries(self, req, stream, data, xpath_prefix=''):
        #self.log.debug('svnmultiurls: dir_entries filename: "%s"', filename)
        # add table cells
        b = StreamBuffer()
        xpath = "//td[@class='%s']"
        stream |= Transformer(xpath_prefix + (xpath % 'name') + "/a/@href").copy(b).end().select(xpath_prefix + (xpath % self.element_class)).after(self.GenerateSVNUrl(b, self.svn_base_url, self.link_text, data['path_links'][0]['href']))
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

        #self.log.debug('svnmultiurls: filter_stream link: "%s"', get('href'))
 
        handlers = { 'browser.html': self.browser,
                     'dir_entries.html': self.dir_entries,
                   }

        if svn_base_url:
            handler = handlers.get(filename, lambda req, stream, data: stream)
            return handler(req, stream, data)
    
        return stream

