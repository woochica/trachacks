from trac.env import open_environment
from trac.config import Configuration, Section
from trac.util.compat import set, all, reversed

from UserDict import DictMixin
import os
import sys
import time
import traceback
import itertools

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
        
        cursor.execute('DELETE FROM tracforge_members WHERE project=%s AND username=%s',(self.name, key))
        
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
    
    def __init__(self, cursor, project, direction, action, stream, step_direction):
        self.cursor = cursor
        self.project = project
        self.direction = direction
        self.action = action
        self.stream = stream
        self.step_direction = step_direction

    def write(self, msg):
        self.cursor.execute('INSERT INTO tracforge_project_output ' \
            '(ts, project, direction, action, stream, step_direction, data) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (time.time(), self.project, self.direction, self.action, self.stream, self.step_direction, msg))


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

    def execute(self, data, direction='execute', project=None):
        """Run this prototype on a new project.
        NOTE: If you pass in a project that isn't new, this could explode. Don't do that.
        """
        from api import TracForgeAdminSystem
        steps = TracForgeAdminSystem(self.env).get_project_setup_participants()
        
        # Store this for later
        orig_direction = direction
        
        # Clear out the last attempt at making this project, if any
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('DELETE FROM tracforge_project_log WHERE project=%s AND direction=%s', (data['name'], direction))
        cursor.execute('DELETE FROM tracforge_project_output WHERE project=%s AND direction=%s', (data['name'], direction))
        db.commit()
        
        # Grab the current stdout/err
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        if direction == 'execute':
            run_buffer = [(action, args, 'execute') for action, args in self]
        else:
            cursor.execute('SELECT action, args WHERE project=%s AND direction=%s AND undone=%s ORDER BY step DESC',
                           (project, direction, 0))
            run_buffer = [(action, args, 'undo') for action, args in cursor]

        for i, (action, args, step_direction) in enumerate(run_buffer):
            #print data['name'], orig_direction, action, step_direction
            cursor.execute('INSERT INTO tracforge_project_log (project, step, direction, action, step_direction, args, undone) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                           (data['name'], i, orig_direction, action, step_direction, args, 0))
            db.commit()
            def log_cb(stdout, stderr):
                now = time.time()
                #print '!'1, stdout, '!', stderr
                values = []
                if stdout:
                    values.append((now, data['name'], orig_direction, action, 'stdout', step_direction, stdout))
                if stderr:
                    values.append((now, data['name'], orig_direction, action, 'stderr', step_direction, stderr))
                if values:
                    cursor.executemany('INSERT INTO tracforge_project_output ' \
                                 '(ts, project, direction, action, stream, step_direction, data) VALUES ' \
                                 '(%s, %s, %s, %s, %s, %s, %s)',
                     values)
                    db.commit()
            if getattr(steps[action]['provider'], 'capture_output', True):
                sys.stdout = _CaptureOutput(cursor, data['name'], orig_direction, action, 'stdout', step_direction)
                sys.stderr = _CaptureOutput(cursor, data['name'], orig_direction, action, 'stderr', step_direction)
            try:
                rv = getattr(steps[action]['provider'], step_direction+'_setup_action')(action, args, data, log_cb)
            except Exception, e:
                log_cb('', traceback.format_exc())
                rv = False
            cursor.execute('UPDATE tracforge_project_log SET return=%s WHERE project=%s AND direction=%s AND action=%s AND step_direction=%s',
                            (int(rv), data['name'], orig_direction, action, step_direction))
            db.commit()
            
            if not rv and direction == 'execute':
                # Failure, initiate rollback
                direction = 'undo'
                del run_buffer[i+1:]
                run_buffer.extend([(action, args, 'undo') for action, args, _ in reversed(run_buffer)])
        
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    def sort(self):
        """Do an in-place topological sort of this prototype."""
        from api import TracForgeAdminSystem
        steps = TracForgeAdminSystem(self.env).get_project_setup_participants()
        
        all_provides = set()
        for action, args in self:
            all_provides |= set(steps[action].get('provides', ()))
        
        effective_depends = {}
        for action, args in self:
            # All real deps are always used
            effective_depends.setdefault(action, []).extend(steps[action].get('depends', ()))
            for tag in steps[action].get('optional_depends', ()):
                # Any optional dep that is provided by something else is used
                if tag in all_provides:
                    effective_depends[action].append(tag)
        
        old = set([action for action, args in self])
        new = []
        tags = set()
        for i in xrange(len(self)):
            for action in old:
                self.env.log.debug('TracForge: %s %s %s %s %s', i, action, old, new, tags)
                if all([tag in tags for tag in effective_depends[action]]):
                    new.append(action)
                    tags |= set(steps[action].get('provides', []))
                    old.remove(action)
                    break
            if not old:
                break
        if old:
            raise ValueError('Cant solve')
        action_map = dict(self)
        self[:] = [(action, action_map[action]) for action in new]
                    
    
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
        from api import TracForgeAdminSystem
        steps = TracForgeAdminSystem(env).get_project_setup_participants()
        
        proto = cls(env, '')
        for action, info in steps.iteritems():
            default = info['provider'].get_setup_action_default(action, env)
            if default is not None:
                proto.append((action, default))
        env.log.debug('TracForge: %s', proto)
        proto.sort()
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
