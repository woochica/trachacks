import unittest
from tractagsxmlrpc import WikiTagRPCSystem, TicketTagRPCSystem
from trac.test import EnvironmentStub, Mock
from tractags.api import TagEngine

from tracrpc.api import XMLRPCSystem
from trac.wiki.formatter import wiki_to_oneliner

class TagsXmlRpcTestCase(unittest.TestCase):
    test_data = (('wiki', 'WikiStart', ('foo', 'bar')),
                 ('wiki', 'SandBox', ('bar', 'war')),
                 ('ticket', 1, ('war', 'death')),
                 ('ticket', 2, ('death', 'destruction')),
                 ('ticket', 3, ('foo', 'bar', 'destruction'))
                 )

    
    
    perm=Mock(assert_permission=lambda x: True,has_permission=lambda x: True)
    
    req = Mock(perm=perm, authname='anonymous')
    def _populate_tags(self,ts):
            for tagspace, target, tags in self.test_data:
                tagspace = ts.tagspace(tagspace)
                tagspace.add_tags(self.req, target, tags)
                yield tagspace, target, tags
            
    def setUp(self):
        self.env = EnvironmentStub(default_data=True)
        from trac.log import logger_factory
        self.env.log =logger_factory(logtype='syslog', logfile=None, level='DEBUG', logid='Trac', format=None)
        
        self.env.path = '/'
        self.wiki_tag_rpc_engine = WikiTagRPCSystem(self.env)
        self.ticket_tag_rpc_engine = TicketTagRPCSystem(self.env)
        self.tag_engine = TagEngine(self.env)
        self.tag_engine.upgrade_environment(self.env.get_db_cnx())
        self.xml_rpc_system = XMLRPCSystem(self.env)
                         
        
        # Insert some test tickets
        from trac.ticket.model import Ticket
        for id in (1, 2, 3):
            ticket = Ticket(self.env)
            ticket['summary'] = 'Test ticket %i' % id
            ticket['description'] = 'Test ticket %i description' % id
            ticket.insert()
    def test_insert(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts):
            found_tags = tagspace.get_tags([target])
            self.assertEqual(found_tags, set(tags))  
              
    def test_wiki_tagspace(self):
        
        self.assertEqual(self.wiki_tag_rpc_engine.namespace, 'wiki')
        
    def test_ticket_tagspace(self):
        
        self.assertEqual(self.ticket_tag_rpc_engine.namespace, 'ticket')
        
    def test_wiki_xmlrpc_methods(self):
        self.failUnless(set(self.wiki_tag_rpc_engine.xmlrpc_methods()) != None, "No xmlrpc methods for wiki namespace")
 
    def test_ticket_xmlrpc_methods(self):
        self.failUnless(set(self.ticket_tag_rpc_engine.xmlrpc_methods()) != None, "No xmlrpc methods for ticket namespace")
        
    def test_wiki_xmlrpc_namespace(self):
        self.assertEqual(self.wiki_tag_rpc_engine.xmlrpc_namespace(), "tags.wiki")
        
    def test_ticket_xmlrpc_namespace(self):
        self.assertEqual(self.ticket_tag_rpc_engine.xmlrpc_namespace(), "tags.ticket")  
        
    def test_wiki_get_name_tags (self):
        wiki_start_tags = self.wiki_tag_rpc_engine.getTags(self.req,"WikiStart")
        self.failUnless( wiki_start_tags!= None, "Can not find any tags for mock page WikiStart")
        
        
    def test_xmlrpc_listMethods(self):
        for method in self.xml_rpc_system.all_methods(self.req):
                namespace = method.namespace.replace('.', '_')
                namespaces = {}
                if namespace not in namespaces:
                    namespaces[namespace] = {
                        'description' : wiki_to_oneliner(method.namespace_description, self.env),
                        'methods' : [],
                        'namespace' : method.namespace,
                        }
                try:
                    namespaces[namespace]['methods'].append((method.signature, wiki_to_oneliner(method.description, self.env), method.permission))
                except Exception, e:
                    self.fail('%s: %s\n' % (method.name, str(e)))
                    

        

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagsXmlRpcTestCase, 'test'))
    return suite        

if __name__ == '__main__':
    unittest.main(defaultTest='suite')