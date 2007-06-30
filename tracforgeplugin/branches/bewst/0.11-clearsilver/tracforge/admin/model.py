from trac.env import Environment
from trac.web.main import _open_environment
from trac.config import Configuration, Section

from UserDict import DictMixin
from tempfile import mkstemp, TemporaryFile
import os
import sys

class BadEnv(object):
    def __init__(self, env_path, exc):
        self.env_path = env_path
        self.exc = exc

    def __getattr__(self, key):
        return "Bad environment at '%s' (%s)"%(self.env_path, self.exc)

class Members(object, DictMixin):
    """Model object for TracForge project memberships."""
    
    def __init__(self, env, name, db=None):
        self.env = env
        self.name = name
        
        if db:
            self.handle_commit = False
            self.db = db
        else:
            self.handle_commit = True
            self.db = self.env.get_db_cnx()
        
    def __getitem__(self, key):
        cursor = self.db.cursor()
        
        cursor.execute('SELECT role FROM tracforge_members WHERE project=%s AND sid=%s',(self.name, key))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            cursor.execute('SELECT role FROM tracforge_members WHERE project=%s AND sid=%s',('*', key))
            row = cursor.fetchone()
            if row:
                return row[0]
            else:
                raise KeyError, "User '%s' not found in project '%s'"%(key, self.name)
            
    def __setitem__(self, key, val):
        cursor = self.db.cursor()
        
        cursor.execute('UPDATE tracforge_members SET role=%s WHERE project=%s AND sid=%s',(val, self.name, key))
        if not cursor.rowcount:
            cursor.execute('INSERT INTO tracforge_members (project, sid, role) VALUES (%s, %s, %s)', (self.name, key, val))
            
        if self.handle_commit:
            self.db.commit()
            
    def __delitem__(self, key):
        cursor = self.db.cursor()
        
        cursor.execute('DELETE FROM tracforge_members WHERE project=%s AND sid=%s',(self.name, key))
        
        if self.handle_commit:
            self.db.commit()
            
    def keys(self):
        cursor = self.db.cursor()
        
        cursor.execute('SELECT sid FROM tracforge_members WHERE project=%s',(self.name,))
        for row in cursor:
            yield row[0]

class Project(object):
    """Model object for TracForge projects."""
    
    def __init__(self, env, name, db=None):
        """Create a new Project object. `env` should be the master environment,
        and `name` is shortname for the project."""
        
        self.master_env = env
        self.name = name
        self.env_path = None
        self._env = None
        self._valid = False
        self.members = Members(self.master_env, self.name, db)
        
        db = db or self.master_env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT env_path FROM tracforge_projects WHERE name=%s',(self.name,))
        row = cursor.fetchone()
        if row:
            self.env_path = row[0]
            
    exists = property(lambda self: self.env_path is not None)
    
    def _get_env(self):
        if not self._env:
            assert self.exists, "Can't use a non-existant project"
            try:
                self._env = _open_environment(self.env_path)
                self._valid = True
            except Exception, e:
                self._env = BadEnv(self.env_path, e)
        return self._env
    env = property(_get_env)    
    
    def _get_valid(self):
        unused = self.env # This will make sure that we have tried loading the env at least once
        return self._valid
    valid = property(_get_valid)
        
    def save(self, db=None):
        handle_commit = False
        if not db:
            db = self.master_env.get_db_cnx()
            handle_commit = True
        cursor = db.cursor()
        
        
        cursor.execute('UPDATE tracforge_projects SET env_path=%s WHERE name=%s',(self.env_path or '', self.name))
        if not cursor.rowcount:
            cursor.execute('INSERT INTO tracforge_projects (name, env_path) VALUES (%s, %s)',(self.name, self.env_path or ''))
            
        if handle_commit:
            db.commit()
    
    def delete(self, db=None):
        assert self.exists
        handle_commit = False
        if not db:
            db = self.master_env.get_db_cnx()
            handle_commit = True
        cursor = db.cursor()
        
        cursor.execute('DELETE FROM tracforge_projects WHERE name=%s',(self.name,))    
            
        if handle_commit:
            db.commit()


    def __contains__(self, key):
        """Allow the nice syntax of `if 'sid' in project:`"""
        return self.members.__contains__(key)    

    def select(cls, env, db=None):
        """Find all known project shortnames."""
        db = db or env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name FROM tracforge_projects')
        for row in cursor:
            yield row[0]
    select = classmethod(select)            

    def by_env_path(cls, env, env_path, db=None):
        """Find a Project based on its env_path."""
        db = db or env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute('SELECT name FROM tracforge_projects WHERE env_path=%s',(env_path,))
        row = cursor.fetchone()
        
        name = ''
        if row:
            name = row[0]
        return Project(env, name, db)
    by_env_path = classmethod(by_env_path)            

class Prototype(list):
    """A model object for a project prototype."""
    
    def __init__(self, env, tag, db=None):
        """Initialize a new Prototype. `env in the master environment."""
        self.env = env
        self.tag = tag
        
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute('SELECT action, args FROM tracforge_prototypes WHERE tag=%s ORDER BY step', (self.tag,))
        list.__init__(self,[{'action':action, 'args':args} for action,args in cursor.fetchall()])

    exists = property(lambda self: len(self)>0)
        
    def save(self, db=None):
        handle_commit = False
        if not db:
            db = self.env.get_db_cnx()
            handle_commit = True
        cursor = db.cursor()
        
        cursor.execute('DELETE FROM tracforge_prototypes WHERE tag=%s', (self.tag,))
        for data, i in zip(self, xrange(len(self))):
            action = args = None
            if isinstance(data, dict):
                action = data['action']
                args = data['args']
            elif isinstance(data, (tuple, list)):
                action = data[0]
                args = data[1]
            else:
                raise TypeError('Invalid type %s in prototype'%type(data))
            cursor.execute('INSERT INTO tracforge_prototypes (tag, step, action, args) VALUES (%s, %s, %s, %s)', (self.tag, i, action, args))
            
        if handle_commit:
            db.commit()
            
    def delete(self, db=None):
        """Remove a prototype from the database."""
        handle_commit = False
        if not db:
            db = self.env.get_db_cnx()
            handle_commit = True
        cursor = db.cursor()
        
        cursor.execute('DELETE FROM tracforge_prototypes WHERE tag=%s', (self.tag,))
        
        if handle_commit:
            db.commit()        
            
    def __contains__(self, other):
        fn = None
        if isinstance(other, (str, unicode)):
            fn = lambda a,b: a == b[0] # Check if the string is an action in this prototype
        elif isinstance(other, (tuple, list)):
            fn = lambda a,b: a[0] == b[0] and a[1] == b[1]
        elif isinstance(other, dict):
            fn = lambda a,b: a['action'] == b[0] and a['args'] == b[1]

        for x in self:
            if isinstance(x, dict):
                x = (x['action'], x['args'])
            if fn(other, x):
                return True
        return False        

    def apply(self, req, proj):
        """Run this prototype on a new project.
        NOTE: If you pass in a project that isn't new, this could explode. Don't do that.
        """
        from api import TracForgeAdminSystem
        steps = TracForgeAdminSystem(self.env).get_project_setup_participants()
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('DELETE FROM tracforge_project_log WHERE project=%s', (proj.name,))
        db.commit()

        for step in self:
            action = args = None
            if isinstance(step, dict):
                action = step['action']
                args = step['args']
            else:
                action, args = step
                
            pid = os.fork()
            if not pid:
                #o_fd, o_file = mkstemp('tracforge-step', text=True)
                #e_fd, e_file = mkstemp('tracforge-step', text=True)
                
                o_file = TemporaryFile(prefix='tracforge-step', bufsize=0)
                e_file = TemporaryFile(prefix='tracforge-step', bufsize=0)
                
                sys.stdout = o_file
                sys.stderr = e_file
                
                os.dup2(o_file.fileno(), 1)
                os.dup2(e_file.fileno(), 2)
            
                rv = steps[action]['provider'].execute_setup_action(req, proj, action, args)
                self.env.log.debug('TracForge: %s() => %r', action, rv)
                
                o_file.seek(0,0)
                o_data = o_file.read()
                o_file.close()
                e_file.seek(0,0)
                e_data = e_file.read()
                e_file.close()
                
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                cursor.execute('INSERT INTO tracforge_project_log (project, action, args, return, stdout, stderr) VALUES (%s, %s, %s, %s, %s, %s)',
                               (proj.name, action, args, unicode(rv), o_data, e_data))
                db.commit()
                db.close()
                
                os._exit(0)
        os.waitpid(pid, 0)


    def select(cls, env, db=None):
        """Return an iterable of valid tags."""
        db = db or env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute('SELECT DISTINCT tag FROM tracforge_prototypes')
        for row in cursor:
            yield row[0]
    select = classmethod(select)
    
    def default(cls, env):
        """Return a prototype for the defaults on the new prototype screen."""
        proto = cls(env, '')
        proto.append({'action':'MakeTracEnvironment', 'args':''})
        return proto
    default = classmethod(default)

class ConfigSet(object):
    """A model object for configuration sets used when creating new projects."""
    
    def __init__(self, env, tag, with_star=True, db=None):
        """Initialize a new ConfigSet. `env` is the master environment."""
        self.env = env
        self.tag = tag
        self.with_star = with_star
        
        self._data = {}
        self._del = set()
        
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        sql = 'SELECT section, key, value, action FROM tracforge_configs WHERE tag=%s'
        args = [self.tag]
        if with_star:
            sql += ' OR tag=%s'
            args.append('*')
        
        cursor.execute(sql, args)
        for section, name, value, action in cursor:
            self._data.setdefault(section, {})[name] = (value, action)
            
    def __contains__(self, key):
        return key in self._data
        
    def remove(self, section, name):
        if section in self._data and name in self._data[section]:
            del self._data[section][name] 
        self._del.add((section, name))
    
    def sections(self):
        return sorted(self._data.iterkeys())
        
    def get(self, section, action=None, with_action=False):
        cond_fn = lambda x: True
        if action is not None:
            cond_fn = lambda x: x == action
            
        format_fn = lambda x: x[0]
        if with_action:
            format_fn = lambda x: x
            
        return dict([(k, format_fn(v)) for k,v in self._data[section].iteritems() if cond_fn(v[1])])
    
    def set(self, section, key, value, action='add'):
        self._data.setdefault(section, {})[key] = (value, action)
        self._del.discard((section, key))
    
    def save(self, db=None):
        assert not self.with_star, "Not sure how to handle this yet."

        handle_commit = False
        if db is None:
            db = self.env.get_db_cnx()
            handle_commit = True
        cursor = db.cursor()
        
        for section, key in self._del:
            cursor.execute('DELETE FROM tracforge_configs WHERE tag=%s AND section=%s AND key=%s', (self.tag, section, key))
        self._del.clear()
        
        for section, x in self._data.iteritems():
            for key, (value, action) in x.iteritems():
                cursor.execute('UPDATE tracforge_configs SET value=%s, action=%s WHERE tag=%s AND section=%s AND key=%s',
                               (value, action, self.tag, section, key))
                if not cursor.rowcount:
                    cursor.execute('INSERT INTO tracforge_configs (tag, section, key, value, action) VALUES (%s, %s, %s, %s, %s)',
                                   (self.tag, section, key, value, action))
                                   
        if handle_commit:
            db.commit()

    def select(cls, env, db=None):
        """Return all tags in the database."""
        db = db or env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT DISTINCT tag FROM tracforge_configs')
        for tag, in cursor:
            if tag != '*':
                yield tag
    select = classmethod(select)
