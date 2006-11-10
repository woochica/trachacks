# Model objects for TracBL
#  Overkill, probably ;-)

from trac.notification import NotifyEmail
from trac.util import hex_entropy

class Key(object):
    """A model object for an API key."""
    
    def __init__(self, env, email, db=None):
        self.env = env
        self.email = email
        
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute('SELECT key FROM tracbl_apikeys WHERE email=%s', (self.email,))
        row = cursor.fetchone()
        if row:
            self.key = row[0]
            self.exists = True
        else:
            self.key = None
            self.exists = False
            
    def valid(cls, env, key, db=None):
        """Check if the given key is valid."""
        db = db or env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM tracbl_apikeys WHERE key=%s', (key,))
        count = cursor.fetchone()[0]
        return count > 0
    valid = classmethod(valid)

    def save(self, db=None):
        handle_commit = False
        if db is None:
            db = self.env.get_db_cnx()
            handle_commit = True
        cursor = db.cursor()
        
        if self.key is None:
            self.key = hex_entropy(16)
            
        if self.exists:
            cursor.execute('UPDATE tracbl_apikeys SET key=%s WHERE email=%s', (self.key, self.email)) # ???: Is this needed?
        else:
            cursor.execute('INSERT INTO tracbl_apikeys (email, key) VALUES (%s, %s)', (self.email, self.key))
            
        if handle_commit:
            db.commit()

    def notify(self):
        """Send an email about this key."""
        eml = KeyEmail(self.env)
        eml.notify(self.email, self.key)

class KeyEmail(NotifyEmail):
    """An email containing an API key."""
    
    template_name = 'tracbl_key_email.cs'
    
    def notify(self, to, key):
        addr = self.get_smtp_address(to)
        if addr is None:
            raise TracError('Invalid email address %s'%to)
        
        
        self.hdf['to'] = addr
        self.hdf['key'] = key
        
        subject = 'TracBL API key for %s'%addr
        
        NotifyEmail.notify(self, addr, subject)

    def get_recipients(self, to):
        return [to], []
