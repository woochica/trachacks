from trac.env import open_environment
from trac.config import Configuration, Section

from UserDict import DictMixin
import os
import sys
import time
import traceback

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
        
        cursor.execute('SELECT role FROM tracforge_members WHERE project=%s AND username=%s',(self.name, key))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            cursor.execute('SELECT role FROM tracforge_members WHERE project=%s AND username=%s',('*', key))
            row = cursor.fetchone()
            if row:
                return row[0]
            else:
                raise KeyError, "User '%s' not found in project '%s'"%(key, self.name)
            
    def __setitem__(self, key, val):
        cursor = self.db.cursor()
        
        cursor.execute('UPDATE tracforge_members SET role=%s WHERE project=%s AND username=%s',(val, self.name, key))
        if not cursor.rowcount:
            cursor.execute('INSERT INTO tracforge_members (project, username, role) VALUES (%s, %s, %s)', (self.name, key, val))
            
        if self.handle_commit:
            self.db.commit()
            
    def __delitem__(self, key):
        cursor = self.db.cursor()
        
        cursor.execute('DELETE FROM tracforge_members WHERE project=%s AND user=%s',(self.name, key))
        
        if self.handle_commit:
            self.db.commit()
            
    def keys(self):
        cursor = self.db.cursor()
        
        cursor.execute('SELECT username FROM tracforge_members WHERE project=%s',(self.name,))
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
                self._env = open_environment(self.env_path, use_cache=True)
                self._valid = True
            except Exception, e:
                self._env = BadEnv(self.env_path, e)
        return self._env
    env = property(_get_env)    

    def _get_valid(self):
        self._get_env() # This will make sure that we have tried loading the env at least once
        return self._valid
    valid = property(_get_valid)

    full_name = property(lambda self: self.valid and self.env.project_name or '')

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

    def select(cls, env, db=None):
        """Find all known project shortnames."""
        db = db or env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name FROM tracforge_projects')
        for row in cursor:
            yield row[0]
    select = classmethod(select)            

    # XXX: Should be from_env_path <NPK>
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


class _CaptureOutput(object):
    """A file-like object to replace sys.stdout/err."""
    
    def __init__(self, cursor, project, action, stream):
        self.cursor = cursor
        self.project = project
        self.action = action
        self.stream = stream

    def write(self, msg):
        self.cursor.execute('INSERT INTO tracforge_project_output ' \
            '(ts, project, action, stream, data) VALUES (%s, %s, %s, %s, %s)',
            (time.time(), self.project, self.action, self.stream, msg))


class Prototype(list):
    """A model object for a project prototype."""
    
    def __init__(self, env, tag, db=None):
        """Initialize a new Prototype. `env` is the master environment."""
        self.env = env
        self.tag = tag
        
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute('SELECT action, args FROM tracforge_prototypes WHERE tag=%s ORDER BY step', (self.tag,))
        list.__init__(self, cursor)

    exists = property(lambda self: len(self)>0)
        
    def save(self, db=None):
        handle_commit = False
        if not db:
            db = self.env.get_db_cnx()
            handle_commit = True
        cursor = db.cursor()
        
        cursor.execute('DELETE FROM tracforge_prototypes WHERE tag=%s', (self.tag,))
        for i, data in enumerate(self):
            cursor.execute('INSERT INTO tracforge_prototypes (tag, step, action, args) VALUES (%s, %s, %s, %s)', (self.tag, i, data[0], data[1]))
            
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
        if isinstance(other, basestring):
            fn = lambda a,b: a == b[0] # Check if the string is an action in this prototype
        else:
            fn = lambda a,b: a[0] == b[0] and a[1] == b[1]

        for x in self:
            if fn(other, x):
                return True
        return False        

    def execute(self, data):
        """Run this prototype on a new project.
        NOTE: If you pass in a project that isn't new, this could explode. Don't do that.
        """
        from api import TracForgeAdminSystem
        steps = TracForgeAdminSystem(self.env).get_project_setup_participants()
        
        # Clear out the last attempt at making this project, if any
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('DELETE FROM tracforge_project_log WHERE project=%s', (data['name'],))
        cursor.execute('DELETE FROM tracforge_project_output WHERE project=%s', (data['name'],))
        db.commit()
        
        # Grab the current stdout/err
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        for i, (action, args) in enumerate(self):
            cursor.execute('INSERT INTO tracforge_project_log (project, step, action, args) VALUES (%s, %s, %s, %s)',
                           (data['name'], i, action, args))
            db.commit()
            def log_cb(stdout, stderr):
                now = time.time()
                #print '!', stdout, '!', stderr
                values = []
                if stdout:
                    values.append((now, data['name'], action, 'stdout', stdout))
                if stderr:
                    values.append((now, data['name'], action, 'stderr', stderr))
                if values:
                    cursor.executemany('INSERT INTO tracforge_project_output ' \
                                 '(ts, project, action, stream, data) VALUES ' \
                                 '(%s, %s, %s, %s, %s)',
                     values)
                    db.commit()
            if getattr(steps[action]['provider'], 'capture_output', True):
                sys.stdout = _CaptureOutput(cursor, data['name'], action, 'stdout')
                sys.stderr = _CaptureOutput(cursor, data['name'], action, 'stderr')
            try:
                rv = steps[action]['provider'].execute_setup_action(action, args, data, log_cb)
            except Exception, e:
                log_cb('', traceback.format_exc())
                rv = False
            cursor.execute('UPDATE tracforge_project_log SET return=%s WHERE project=%s AND action=%s',
                            (rv, data['name'], action))
            db.commit()
        
        sys.stdout = old_stdout
        sys.stderr = old_stderr


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
