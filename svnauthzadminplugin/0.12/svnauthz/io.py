# -*- coding: utf-8 -*-

import os
from model import *

class AuthzFileReader:
    def __init__(self):
        pass
    
    def read(self, filename):
        fp = open(filename, "r")
        parser = AuthzFileParser(filename, fp)
        return parser.parse()

    
class AuthzFileWriter:
    def __init__(self):
        pass

    def write(self, filename, model):
        fp = open(filename, "r")
        orig = fp.read()
        fp.close()
        new = model.serialize()
        if (orig != new):
            fp = open(filename, "w")
            fp.write(new)
            fp.close()




PARSE_NORMAL = 0
PARSE_GROUPS = 1
PARSE_PATH_ACL = 2


class AuthzFileParser:
    
    
    def __init__(self, filename, fp):
        self.filename = filename
        self.fp = fp
        self.state = PARSE_NORMAL
    
    def parse(self):
        try:
            m = AuthModel(self.filename, [], [])
            self.state = PARSE_NORMAL
            self._parse_root(m)
            return m        
        finally:
            self.fp.close()
    
        
    def _parse_root(self, m):
        while True:
            line = self.fp.readline()
            if (line == ""):
                break
            line = line.strip()
            if line.startswith("#"):
                # Ignore comments
                continue
            if (len(line) == 0):
                continue
            if line == "[groups]":
                self.state = PARSE_GROUPS
                continue
            else:
                if line.startswith("["):
                    self._parse_path(m, line)
                    self.state = PARSE_PATH_ACL
                    continue
            if self.state == PARSE_GROUPS:
                self._parse_group(m, line)
            else:
                if self.state == PARSE_PATH_ACL:
                    self._parse_path_acl(m, line)

    def _parse_group(self, m, line):
        groupname, memberstr = line.split("=")
        groupname = groupname.strip()
        g = m.find_group(groupname)
        if g == None:
            g = Group(groupname, [])
            m.add_group(g)

        memberstr = memberstr.strip()
        if len(memberstr) == 0:
            return
        if "," in memberstr:
            members = memberstr.split(",")
        else:
            members = [memberstr]
        for me in members:
            me = me.strip()
            if me.startswith("@"):
                
                memberg = m.find_group(me.lstrip("@"))
                if memberg == None:
                    memberg = Group(me.lstrip("@"), [])
                    m.add_group(memberg)
                g.append(memberg)
            else:
                g.append(User(me))
            
    def _parse_path(self, m, line):
        line = line.lstrip("[").rstrip("]")
        if ":" in line:
            repo, path = line.split(":")
            repo = repo.strip()
            path = path.strip()
        else:
            repo = None
            path = line.strip()
        self.current_path = Path(path, [], repo)
        assert(m.find_path(self.current_path) == [])
        m.add_path(self.current_path)

    def _parse_path_acl(self, m, line):
        subjectstr, aclstr = line.split("=")
        acl = [False, False]
        if (aclstr != None):
            if "r" in aclstr:
                acl[0] = True
            if "w" in aclstr:
                acl[1] = True
        subjectstr = subjectstr.strip()
        assert (len(subjectstr) > 0)        
        if subjectstr.startswith("@"):            
            assert (len(subjectstr) > 1)        
            subject = m.find_group(subjectstr.lstrip("@"), True)
            assert (subject != None)
        else:
            subject = User(subjectstr)
        self.current_path.append(PathAcl(subject, *acl))
