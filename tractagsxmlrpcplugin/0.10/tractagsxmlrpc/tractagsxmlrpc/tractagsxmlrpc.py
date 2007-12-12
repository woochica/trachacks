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
from tracrpc.api import IXMLRPCHandler, expose_rpc
from tracrpc.util import to_timestamp
from tractags.api import DefaultTaggingSystem
from tractags.api import TagEngine
from tractags.wiki import WikiTags
from tractags.ticket import TicketTags
import types


class BaseTagRPCSystem(object):
      
    def __init__(self,env):
        self.env = env
        
        
    def xmlrpc_namespace(self):
        return "tags.%s" % (self.namespace)
            
    def xmlrpc_methods(self):
        #self.env.log.debug("Returning xmlrpc methods for %s" %self.namespace)
        
        yield ('XML_RPC', ((bool,str,dict),), self.addTags)
        yield ('XML_RPC', ((bool,str,dict),), self.removeTags)      
        yield ('XML_RPC', ((bool,str),), self.removeAllTags)
        yield ('XML_RPC', ((bool,str,dict),), self.replaceTags)
        yield ('XML_RPC', ((dict,str),), self.getNames)       
        yield ('XML_RPC', ((dict,str),), self.nameDetails)
        yield ('XML_RPC', ((dict,str),), self.getTags)

        
    def getTags(self,req,name):
        """ Get tags for a wiki page name, or a ticket name. """
        self.env.log.debug("Returning tags for name %s: %s"%(name,self.tagsystem.get_name_tags(name)))
        return self.tagsystem.get_name_tags(name)

    def addTags(self, req, name, tags):
        """ Tag name in tagsystem with tags. """
        self.env.log.debug("Adding tags (%s) to name %s: %s"%(tags,name,self.tagsystem.get_name_tags(name)))
        try:
            self.tagsystem.add_tags(req,name,tags)
            return True
        except Exception, e:
            self.env.log.debug('%s: %s\n' % (name, str(e)))
            return  False


    def replaceTags(self, req, name, tags):
        """ Replace existing tags on name with tags. """
        self.env.log.debug("Replacing tags (%s) to name %s: %s"%(tags,name,self.tagsystem.get_name_tags(name)))
        self.tagsystem.remove_all_tags(req, name)
        self.tagsystem.add_tags(req, name, tags)

    def removeTags(self, req, name, tags):
        self.env.log.debug("Removing tags (%s) to name %s: %s"%(tags,name,self.tagsystem.get_name_tags(name)))
        """ Remove tags from a name in a tagsystem. """
        return self.tagsystem.remove_tags(req,name,tags)

    def removeAllTags(self, req, name):
        self.env.log.debug("Removing all tags from name %s: %s"%(name,self.tagsystem.get_name_tags(name)))
        """ Remove all tags from a name in a tagsystem. """
        try :
            self.tagsystem.remove_all_tags(req,name)
            return True
        except Exception, e:
            self.env.log.debug('%s: %s\n' % (name, str(e)))
            return  False

        

    def nameDetails(self, req, name):
        """ Return a tuple of (href, htmllink, title). eg. 
            ("/ticket/1", "<a href="/ticket/1">#1</a>", "Broken links") or
             ("/wiki/WikiStart", "<a class="wiki" href="/wiki/WikiStart">WikiStart</a>", "Welcome to trac")"""
        self.env.log.debug("Calling nameDetails for %s "%name)    
        href,htmllink,title = self.tagsystem.name_details(name)
        #href = href.__call__()
       
        if type(href) ==types.FunctionType:
            self.env.log.debug("href is a function")
            href = href.__call__()
        self.env.log.debug('  found  %s %s %s '%(href,htmllink,title)) 
        return ("%s"%href,"%s"%htmllink,"%s"%title)
    
    def getNames(self, req, tagname):
        """ Returns all pages with tagname """
        engine = TagEngine(self.env)
        try:
            tagspaces = list()
            tagspaces.append(self.tagsystem.tagspace)
            tags = list()
            tags.append (tagname)
            names = engine.get_tagged_names(tags=tags,tagspaces=tagspaces)
            self.env.log.debug("getNames found %s for tagname %s"%(names, tagname))
            return list(names[self.tagsystem.tagspace])
        except Exception, e:
            self.env.log.debug('Error in getNames(%s): %s\n' % (tagname, str(e)))
            return None
        
class WikiTagRPCSystem(BaseTagRPCSystem,Component):
    """ Interface to tags for the wiki system"""
    implements(IXMLRPCHandler)
    def __init__(self):
        BaseTagRPCSystem.__init__(self,self.env)
        temp =WikiTags(self.env)
        self.tagsystem = temp.get_tagging_system("wiki")
        self.namespace = "wiki"
        
class TicketTagRPCSystem(BaseTagRPCSystem,Component):
    """ Interface to tags for the ticket system"""
    implements(IXMLRPCHandler)
    def __init__(self):
        BaseTagRPCSystem.__init__(self,self.env)
        temp =TicketTags(self.env)
        self.tagsystem = temp.get_tagging_system("ticket")
        self.namespace = "ticket"
        
        