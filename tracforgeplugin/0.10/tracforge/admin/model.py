class Project(object):
    """Model object for TracForge projects."""
    
    def __init__(self, env, name, db=None):
        """Create a new Project. `env` should be the master environment,
        and `name` is shortname for the project."""
        
        self.master_env = env
        self.name = name
        self.env_path = None
        self._env = None
        
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
            self._env = Environment(self.env_path)
        return self._env
    env = property(_get_env)    
        
            
    @classmethod
    def select(cls, env, db=None):
        db = db or env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name FROM tracforce_projects')
        for row in cursor:
            yield row[0]
            
