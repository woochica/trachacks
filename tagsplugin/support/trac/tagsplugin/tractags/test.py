import unittest

from trac.test import EnvironmentStub, Mock
from tractags.api import TagEngine
import time

# We need to fake time (heh), otherwise the ticket saves violate column
# constraints because the time for two discrete changes is the same.
class fake_time(object):
    _the_time = 0

    def __call__(self):
        self._the_time += 1
        return self._the_time
time.time = fake_time()

try:
    set = set
except:
    from sets import Set as set

class TagApiTestCase(unittest.TestCase):
    test_data = (('wiki', 'WikiStart', ('foo', 'bar')),
                 ('wiki', 'SandBox', ('bar', 'war')),
                 ('ticket', 1, ('war', 'death')),
                 ('ticket', 2, ('death', 'destruction')),
                 ('ticket', 3, ('foo', 'bar', 'destruction'))
                 )

    req = Mock(perm=Mock(assert_permission=lambda x: True),
               authname='anonymous')

    def _populate_tags(self, ts):
        for tagspace, target, tags in self.test_data:
            tagspace = ts.tagspace(tagspace)
            tagspace.add_tags(self.req, target, tags)
            yield tagspace, target, tags

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
            ticket.insert()

    def test_tagspaces(self):
        tagspaces = set(self.tag_engine.tagspaces)
        self.assertEqual(tagspaces, set(('ticket', 'wiki')))

    def test_insert(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts):
            found_tags = tagspace.get_tags([target])
            self.assertEqual(found_tags, set(tags))

    def test_remove(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts):
            target_tags = tagspace.get_name_tags(target)
            tag = iter(target_tags).next()
            tagspace.remove_tags(self.req, target, (tag,))
            target_tags.discard(tag)
            self.assertEqual(tagspace.get_name_tags(target), target_tags)

    def test_remove_all(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts):
            tagspace.remove_all_tags(self.req, target)

    def test_replace(self):
        ts = self.tag_engine.tagspace
        test_set = set(('foozle', 'stick'))
        for tagspace, target, tags in self._populate_tags(ts):
            found_tags = tagspace.get_tags([target])
            tagspace.replace_tags(self.req, target, test_set)
            self.assertEqual(test_set, tagspace.get_name_tags(target))

    def test_add(self):
        ts = self.tag_engine.tagspace
        test_set = set(('foozle', 'stick'))
        for tagspace, target, tags in self._populate_tags(ts):
            found_tags = tagspace.get_tags([target])
            tagspace.add_tags(self.req, target, test_set)
            self.assertEqual(test_set.union(found_tags), tagspace.get_name_tags(target))

    def test_walk(self):
        engine = self.tag_engine
        compare_data = {}
        for tagspace, target, tags in self._populate_tags(engine.tagspace):
            compare_data.setdefault(tagspace.tagspace, {})[target] = set(tags)
        tag_data = {}
        for tagspace, name, tags in engine.walk_tagged_names():
            tag_data.setdefault(tagspace, {})[name] = tags
        self.assertEqual(compare_data, tag_data)

    def test_get_tagged_union(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts): pass
        self.assertEqual(self.tag_engine.get_tagged_names(tags=('foo', 'bar'), operation='union'),
                         {'wiki': set([u'WikiStart', u'SandBox']), 'ticket': set([3])})

    def test_get_tagged_intersection(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts): pass
        self.assertEqual(self.tag_engine.get_tagged_names(tags=('foo', 'bar'), operation='intersection'),
                         {'wiki': set(['WikiStart']), 'ticket': set([3])})

    def test_get_tags_union(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts): pass
        self.assertEqual(self.tag_engine.get_tags(names=('WikiStart', 1), operation='union'),
                         set(['death', 'bar', 'war', 'foo']))

    def test_get_tags_intersection(self):
        ts = self.tag_engine.tagspace
        for tagspace, target, tags in self._populate_tags(ts): pass
        self.assertEqual(self.tag_engine.get_tags(names=('WikiStart', 3), operation='intersection'),
                         set(['bar', 'foo']))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagApiTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
