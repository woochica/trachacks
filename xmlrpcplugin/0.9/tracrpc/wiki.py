from trac.core import Component, implements
from trac.wiki.api import WikiSystem
from tracrpc.api import IXMLRPCHandler

class WikiRpc(Component):
    implements(IXMLRPCHandler)

    def __init__(self):
        self.wiki = WikiSystem(self.env)

    def get_xmlrpc_functions(self):
        return [('WIKI_VIEW', rpc, 'wiki.' + rpc.__name__) for rpc in (self.getRecentChanges, self.getRPCVersionSupported, self.getPage, self.getPageVersion, self.getPageInfoVersion, self.getPageInfo, self.getAllPages)]

    def _to_timestamp(self, datetime):
        import time
        return time.mktime(time.strptime(datetime.value, '%Y%m%dT%H:%M:%S'))

    def _page_info(self, name, time, author, version):
        return dict(name=name, lastModified=xmlrpclib.DateTime(int(time)),
                    author=author, version=int(version))

    def getRecentChanges(self, since):
        """ Get list of changed pages since timestamp, which should be in UTC. The result is an array, where each element is a struct:

            * name (utf8) : Name of the page.
            * lastModified (date) : Date of last modification, in UTC.
            * author (utf8) : Name of the author (if available).
            * version (int) : Current version.
        """
        since = self._to_timestamp(since)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name, max(time), author, version FROM wiki'
                       ' WHERE time >= %s GROUP BY name ORDER BY max(time) DESC', since)
        result = []
        for name, time, author, version in cursor:
            result.append(self._page_info(name, time, author, version))
        return result

    def getRPCVersionSupported(self):
        """Returns 2 with this version of the Trac API. """
        return 2

    def getPage(self, pagename, version=None):
        """ Get the raw Wiki text of page, latest version. """
        page = WikiPage(self.env, pagename, version)
        if page.exists:
            return page.text
        else:
            msg = 'Wiki page "%s" does not exist' % pagename
            if version is not None:
                msg += ' at version %s' % version
            raise xmlrpclib.Fault(0, msg)

    getPageVersion = getPage

    def getPageHTML(self, pagename, version=None):
        """ Return page in rendered HTML, latest version. """
        pass

    getPageHTMLVersion = getPageHTML

    def getAllPages(self):
        '''
        Returns a list of all pages.
        The result is an array of utf8 pagenames.
        '''
        return list(self.wiki.get_pages())

    def getPageInfo(self, pagename, version=None):
        """ returns a struct with elements

            * name (utf8): the canonical page name.
            * lastModified (date): Last modification date, UTC.
            * author (utf8): author name.
            * version (int): current version 
        """
        page = WikiPage(self.env, pagename, version)
        if page.exists:
            return self._page_info(page.name, page.time, page.author,
                                   page.version)

    getPageInfoVersion = getPageInfo

    def listLinks(self, pagename):
        """ Lists all links for a given page. The returned array contains structs, with the following elements: """
        pass
