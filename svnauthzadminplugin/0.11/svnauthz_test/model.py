import unittest

from svnauthz.model import *

class MemberTest(unittest.TestCase):

    def test_member_name(self):
        self.assertRaises(AssertionError, Member, None)
        self.assertRaises(AssertionError, Member, "            ")
        
    def test_equality(self):
        self.assertEquals(Member("a"),Member("a"))
        self.assertNotEquals(Member("a"), Member("b"))
        
class GroupTest(unittest.TestCase):
    def test_group_name(self):
        self.assertRaises(AssertionError, Group, None)
        self.assertRaises(AssertionError, Group, "            ")

    def test_group_members(self):
        self.failUnless(isinstance(Group("test", None), Group))
        self.failUnless(isinstance(Group("test", []), Group))
        
        self.assertRaises(AssertionError, Group, "test", ["blabla"])
        g = Group("test", [Member("zuzu")])
        self.failUnless(isinstance(g, Group))
        self.assertEquals(g[0], Member("zuzu"))

    def test_equality(self):
        self.assertEquals(Group("test",[]), Group("test",[]))
        self.assertEquals(Group("test",[Member("ttt")]), Group("test",[Member("ttt")]))
        self.assertNotEquals(Group("test",[Member("ttt")]), Group("2test",[Member("ttt")]))
        self.assertNotEquals(Group("test",[Member("ttt")]), Group("test",[Member("ttt"),Member("taaa")]))
        self.assertNotEquals(Group("test",[Member("ttt")]), Group("test",[Member("aaa")]))
        self.assertNotEquals(Group("test",[]), Group("test",[Member("aaa")]))
        self.assertNotEquals(Member("test"),Group("test",[Member("aaa")]))
        g = Group("test", [Member("test"), Member("test2"), Member("test")])
        self.assertEquals(g, Group("test", [Member("test"), Member("test2")]))
        g.append(Member("test"))
        self.assertEquals(g, Group("test", [Member("test"), Member("test2")]))        

class PathTest(unittest.TestCase):
    def test_uniq_acls(self):
        p = Path("/bigyoka", [])
        p.append(PathAcl(Group("X"),True, False))
        p.append(PathAcl(Member("Y"), False, False))
        p.append(PathAcl(Group("X"),False, False))
        self.assertEquals(2, len(p))

        p = Path("/bigyoka", [])
        p.append(PathAcl(Group("X"),True, False))
        p.append(PathAcl(Member("Y"), False, False))
        p.append(PathAcl(User("X"),False, False))
        self.assertEquals(3, len(p))


class AuthModelTest(unittest.TestCase):
    def test_unique_path(self):
        m = AuthModel("fname", None, [Path("/1"), Path("/2"), Path("/1")])
        self.assertEquals(2, len(m.get_paths()))

        m = AuthModel("fname", None, [Path("/1", [], "izee"), Path("/2"), Path("/1", [], "izee")])
        self.assertEquals(2, len(m.get_paths()))
    
        m = AuthModel("fname", None, [Path("/1", [], "izee"), Path("/2"), Path("/1", [], "bigyo")])
        self.assertEquals(3, len(m.get_paths()))


    def test_unique_groups(self):
        m = AuthModel("fname", [Group("x1",[]), Group("x2",[]), Group("x1",[])], None)
        self.assertEquals(2, len(m.get_groups()))
        
    def test_find_path(self):
        p = Path("/ize", [])
        p2 = Path("/ize2", [], "bigyo")
        m = AuthModel("fname", [], [p, p2])
        self.assertEquals(None, m.find_path("/bigyo"))
        self.assertEquals(p, m.find_path("/ize"))
        self.assertEquals(None, m.find_path("/ize2"))
        self.assertEquals(p2, m.find_path("/ize2", "bigyo"))

    def test_find_group(self):
        g = Group("ize", [])
        m = AuthModel("fname", [g], [])
        self.assertEquals(None, m.find_group("bigyo"))
        self.assertEquals(g, m.find_group("ize"))
        

class SerializerTest(unittest.TestCase):

    def test_serialize_cmplx(self):
        reference="""
[groups]
alfa = user1,@beta,user2,user4
beta = user4,@gamma
gamma = user5

[/]
@alfa = r
@beta = rw
@gamma = rw
user2 = 

[izee:/bigyo]
@gamma = r
user2 = rw

"""
        gamma = Group("gamma", [User("user5")])
        beta = Group("beta", [User("user4"), gamma])
        alfa = Group("alfa",[User("user1"), beta, User("user2"), User("user4")])
        
        root = Path("/", [PathAcl(alfa, True, False), 
                          PathAcl(beta, True, True), 
                          PathAcl(gamma, True, True), 
                          PathAcl(User("user2"), False, False)]
                          )
        izee_bigyo = Path("/bigyo", [PathAcl(gamma, True, False), PathAcl(User("user2"), True, True)], "izee")
        
        m = AuthModel("fname", [alfa, beta, gamma], [root, izee_bigyo])
        self.assertEquals(reference,m.serialize())
        