# -*- coding: utf-8 -*-

import types

class Member:
    def __init__(self, name=""):
        assert (name and name.strip() != "")
        self.name = name

    def get_name(self):
        return self.name        

    def __eq__(self, obj):
        return self.__class__ == obj.__class__ and self.name == obj.name
    
    def __str__(self):
        return self.name
    
    def serialize(self):
        return self.name

class User(Member):
    def __init__(self, name):
        Member.__init__(self, name)

class UniqueList(list):
    def __init__(self, initial=None, uniqop=None):
        list.__init__(self)
        self.uniqop = uniqop
        if initial and isinstance(initial, list):
            self.extend(initial)

    def extend(self, obj):
        for x in obj:
            self.append(x)
    
    def __add__(self, obj):
        if not obj in self:
            list.__add__(self, obj)
            
    def __contains__(self, obj):
        if not self.uniqop:
            return list.__contains__(self, obj)
        return self.uniqop(self, obj)

    def append(self, obj):
        if not obj in self:
            list.append(self, obj)


class Group(Member, UniqueList):
    def __init__(self, name, members=None):
        Member.__init__(self, name)
        if (not members):
            members = []
        else:
            assert(isinstance(members, list))
        for member in members:
            assert(isinstance(member, Member))
        UniqueList.__init__(self, members)

    def __eq__(self, obj):
        if (Member.__eq__(self, obj)):
            if len(self) != len(obj):
                return False
            import itertools
            for v in itertools.imap(Member.__eq__,self,obj):
                if (not v):
                    return False
            return True
        return False

    def __str__(self):
        return "@" + self.name

    def serialize(self):
        ret = self.name + " = " 
        for elem in self:
            ret += elem.__str__() + ","
        return ret[0:-1]
        
class Path(UniqueList):
    def __init__(self, path, acls=None, repo=None):
        self.path = path
        self.repo = repo
        UniqueList.__init__(self, acls, unique_acl_member)
        
    def get_path(self):
        return self.path
    
    def get_repo(self):
        return self.repo
    
    def find_path_member(self, member):
        for m in self:
            if m.get_member() == member:
                return m
        return None

    def serialize(self):
        ret = "["
        if self.repo:
            ret += self.repo + ":"
        ret += self.path + "]\n"
        for acl in self:
            ret += acl.serialize()
            ret +="\n"
        return ret

class PathAcl:
    def __init__(self, member, r, w):
        assert (isinstance(member, Member))
        self.member = member
        self.set_read(r)
        self.set_write(w)

    def get_member(self):
        return self.member
    
    def is_read(self):
        return self.r
    
    def is_write(self):
        return self.w
    
    def set_read(self, r):
        assert (r == True or r == False)
        self.r = r

    def set_write(self, w):
        assert (w == True or w == False)
        self.w = w
        
    def serialize(self):
        ret=""+ self.member.__str__() + " = "
        if (self.r):
            ret +="r"
        if (self.w):
            ret +="w"
        return ret

class AuthModel:
    def __init__(self, filename, groups=None, paths=None):
        self.filename = filename
        self.groups = UniqueList(groups, unique_group_name)
        self.paths = UniqueList(paths, unique_path_name)
            
    def get_groups(self):
        return self.groups
    
    def get_paths(self):
        return self.paths
    
    def find_group(self, name, creategroup=False):
        for g in self.groups:
            if name == g.get_name():
                return g
        if creategroup:
            g = Group(name, [])
            self.add_group(g)
            return g
        return None
    
    def find_path(self, path, repo=None):
        for p in self.paths:
            if path == p.get_path() and repo == p.get_repo():
                return p
        return []
    
    def add_path(self, p):
        if isinstance(p, Path):           
            self.paths.append(p)

    def del_path(self, p, repo = None):
        if isinstance(p, Path):           
            self.paths.remove(p)
        elif isinstance(p, types.StringTypes):
            rp = self.find_path(p, repo)
            if isinstance(rp, Path):
                self.paths.remove(rp)

    
    def add_group(self, g):
        if isinstance(g, Group):
            self.groups.append(g)
            
    def del_group(self, g):
        if isinstance(g, types.StringTypes):
            g = self.find_group(g)
        assert (isinstance(g, Group))
        self.groups.remove(g)
        for og in self.groups:
            if g in og:
                og.remove(g)
        for p in self.paths:
            for pacl in p:
                if pacl.get_member() == g:
                    p.remove(pacl)
    
    def serialize(self):
        ret = "\n[groups]\n"
        for group in self.groups:
            ret += group.serialize() + "\n"
        ret +="\n"
        for path in self.paths:
            ret+=path.serialize() + "\n"
        return ret


def unique_group_name(list, elem):
    assert (isinstance(elem, Group))
    for x in list:
        if x.get_name() == elem.get_name():
            return True
    return False

def unique_path_name(list, elem):
    assert (isinstance(elem, Path))
    for x in list:
        if x.get_path() == elem.get_path() and x.get_repo() == elem.get_repo():
            return True
    return False

def unique_acl_member(list, elem):
    assert (isinstance(elem, PathAcl))
    for x in list:
        if x.get_member() == elem.get_member():
            return True
    return False
