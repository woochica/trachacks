from trac.env import Environment
from UserDict import DictMixin

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
        
        cursor.execute('SELECT role FROM tracforge_members WHERE project=%s AND user=%s',(self.name, key))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            cursor.execute('SELECT role FROM tracforge_members WHERE project=%s AND user=%s',('*', key))
            row = cursor.fetchone()
            if row:
                return row[0]
            else:
                raise KeyError, "User '%s' not found in project '%s'"%(key, self.name)
            
    def __setitem__(self, key, val):
        cursor = self.db.cursor()
        
        cursor.execute('UPDATE tracforge_members SET role=%s WHERE project=%s AND user=%s',(val, self.name, key))
        if not cursor.rowcount:
            cursor.execute('INSERT INTO tracforge_members (project, user, role) VALUES (%s, %s, %s)', (self.name, key, val))
            
        if self.handle_commit:
            self.db.commit()
            
    def __delitem__(self, key):
        cursor = self.db.cursor()
        
        cursor.execute('DELETE FROM tracforge_members WHERE project=%s AND user=%s',(self.name, key))
        
        if self.handle_commit:
            self.db.commit()
            
    def keys(self):
        cursor = self.db.cursor()
        
        cursor.execute('SELECT user FROM tracforge_members WHERE project=%s',(self.name,))
        for row in cursor:
            yield row[0]

class Project(object):
    """Model object for TracForge projects."""
    
    def __init__(self, env, name, db=None):
        """Create a new Project. `env` should be the master environment,
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
                self._env = Environment(self.env_path)
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
        """Allow the nice syntax of `if 'user' in project:`"""
        return self.members.__contains__(key)    

    @classmethod
    def select(cls, env, db=None):
        """Find all known project shortnames."""
        db = db or env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name FROM tracforge_projects')
        for row in cursor:
            yield row[0]
            

    @classmethod
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
            
