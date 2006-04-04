import unittest

from trac.test import EnvironmentStub, Mock
from tractags.api import TagEngine

try:
    set = set
except:
    from sets import Set as set

#req = Mock(perm=Mock(has_permission=lambda x: 1))

class TagApiTestCase(unittest.TestCase):
    test_data = (('wiki', 'WikiStart', ('foo', 'bar')),
                 ('wiki', 'SandBox', ('bar', 'war')),
                 ('ticket', 1, ('war', 'death')),
                 ('ticket', 2, ('death', 'destruction')),
                 ('ticket', 3, ('destruction', 'restoration')))

    req = Mock(perm=Mock(assert_permission=lambda x: True),
               authname='anonymous')

    def setUp(self):
        self.env = EnvironmentStub(default_data=True)
        self.env.path = '/'
        self.tag_engine = TagEngine(self.env)
        self.tag_engine.upgrade_environment(self.env.get_db_cnx())

        # Insert some test tickets
        from trac.ticket.model import Ticket
        for id in (1, 2, 3):
            ticket = Ticket(self.env)
            ticket['summary'] = 'Test ticket %i' % id
            ticket['description'] = 'Test ticket %i description' % id
            ticket['FOO'] = 10
            ticket.insert()
        
    def test_tagspaces(self):
        tagspaces = set(self.tag_engine.tagspaces)
        self.assertEqual(tagspaces, set(('ticket', 'wiki')))

    def _populate_tags(self, ts):
        for tagspace, target, tags in self.test_data:
            tagspace = ts.tagspace(tagspace)
            tagspace.add_tags(self.req, target, tags)
            yield tagspace, target, tags

    def test_insert(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts):
            found_tags = tagspace.get_tags([target])
            self.assertEqual(found_tags, set(tags))

    def test_remove_all(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts):
            tagspace.remove_all_tags(self.req, target)

    def test_remove(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts):
            found_tags = tagspace.get_tags([target])
            tagspace.remove_tags(self.req, target, found_tags)
            

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagApiTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
