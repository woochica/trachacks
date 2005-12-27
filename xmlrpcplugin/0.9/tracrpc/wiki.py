try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import xmlrpclib
import posixpath

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage
from trac.wiki.formatter import wiki_to_html
from trac.attachment import Attachment
from tracrpc.api import AbstractRPCHandler, expose_rpc

class WikiRPC(AbstractRPCHandler):
    """ Implementation of the [http://www.jspwiki.org/Wiki.jsp?page=WikiRPCInterface2 WikiRPC API]. """

    def __init__(self):
        self.wiki = WikiSystem(self.env)

    def xmlrpc_namespace(self):
        return 'wiki'

    def _to_timestamp(self, datetime):
        import time
        return time.mktime(time.strptime(datetime.value, '%Y%m%dT%H:%M:%S'))

    def _page_info(self, name, time, author, version):
        return dict(name=name, lastModified=xmlrpclib.DateTime(int(time)),
                    author=author, version=int(version))

    @expose_rpc('WIKI_VIEW', dict, xmlrpclib.DateTime)
    def getRecentChanges(self, since):
        """ Get list of changed pages since timestamp """
        since = self._to_timestamp(since)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name, max(time), author, version FROM wiki'
                       ' WHERE time >= %s GROUP BY name ORDER BY max(time) DESC', since)
        result = []
        for name, time, author, version in cursor:
            result.append(self._page_info(name, time, author, version))
        return result

    @expose_rpc('WIKI_VIEW', int)
    def getRPCVersionSupported(self):
        """ Returns 2 with this version of the Trac API. """
        return 2

    @expose_rpc('WIKI_VIEW', str, str)
    @expose_rpc('WIKI_VIEW', str, str, int)
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

    @expose_rpc('WIKI_VIEW', str, str)
    @expose_rpc('WIKI_VIEW', str, str, int)
    def getPageHTML(self, req, pagename, version=None):
        """ Return page in rendered HTML, latest version. """
        text = self.getPage(pagename, version)
        html = wiki_to_html(text, self.env, req, absurls=1)
        return '<html><body>%s</body></html>' % html

    getPageHTMLVersion = getPageHTML

    @expose_rpc('WIKI_VIEW', list)
    def getAllPages(self):
        """ Returns a list of all pages. The result is an array of utf8 pagenames. """
        return list(self.wiki.get_pages())

    @expose_rpc('WIKI_VIEW', dict, str)
    @expose_rpc('WIKI_VIEW', dict, str, int)
    def getPageInfo(self, pagename, version=None):
        """ Returns information about the given page. """
        page = WikiPage(self.env, pagename, version)
        if page.exists:
            return self._page_info(page.name, page.time, page.author,
                                   page.version)

    getPageInfoVersion = getPageInfo

    @expose_rpc('WIKI_VIEW', bool, str, str, dict)
    def putPage(self, req, pagename, content, attributes):
        """ writes the content of the page. """
        page = WikiPage(self.env, pagename)
        if page.readonly:
            req.perm.assert_permission('WIKI_ADMIN')
        elif not page.exists:
            req.perm.assert_permission('WIKI_CREATE')
        else:
            req.perm.assert_permission('WIKI_MODIFY')

        page.text = content
        if req.perm.has_permission('WIKI_ADMIN'):
            page.readonly = attributes.get('readonly') and 1 or 0

        page.save(attributes.get('author', req.authname),
                  attributes.get('comment'),
                  req.remote_addr)
        return True

    @expose_rpc('WIKI_VIEW', list, str)
    def listAttachments(self, pagename):
        """ Lists attachments on a given page. """
        return [pagename + '/' + a.filename for a in Attachment.select(self.env, 'wiki', pagename)]

    @expose_rpc('WIKI_VIEW', xmlrpclib.Binary, str)
    def getAttachment(self, path):
        """ returns the content of an attachment. """
        pagename, filename = posixpath.split(path)
        attachment = Attachment(self.env, 'wiki', pagename, filename)
        return xmlrpclib.Binary(attachment.open().read())

    @expose_rpc('WIKI_MODIFY', bool, str, str, xmlrpclib.Binary)
    def putAttachment(self, path, data):
        """ (over)writes an attachment. """
        pagename, filename = posixpath.split(path)
        if not WikiPage(self.env, pagename).exists:
            raise TracError, 'Wiki page "%s" does not exist' % pagename
        attachment = Attachment(self.env, 'wiki', pagename)
        attachment.insert(filename, StringIO(data.data), len(data.data))
        return True

    @expose_rpc('WIKI_VIEW', list, str)
    def listLinks(self, pagename):
        """ ''Not implemented'' """
        pass
