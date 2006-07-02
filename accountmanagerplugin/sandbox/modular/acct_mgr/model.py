# Account model object

from api import *

class Account(object):
    """A simple model object for a Trac user account."""
    
    def __init__(self, env, username, db=None):
        self.env = env
        self.username = username
        
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        # Try to extract the account status (or set to 'new')
        cursor.execute('SELECT status FROM account_status WHERE user = %s',
                       (self.username,))
        self.status = cursor.fetchone()
        if not self.status:
            self.status = 'new'
            
        # For non-new accounts, find what account store they belong to
        if self.status != 'new':
            for store in AccountSystem(self.env).account_stores:
                if store.has_user(self.username):
                    self.store = store
                    break
            else:
                raise AccountError, "Non-new account that doesn't exist in any store"

    def save(self, db = None):
        db, handle_commit = self._get_db(db)
        cursor = db.cursor()
        
        # Find the old status
        cursor.execute('SELECT status FROM account_status WHERE user = %s', (self.username,))
        old_status = cursor.fetchone()
        if not old_status:
            cursor.execute('INSERT INTO account_status (user, status) VALUES (%s, %s)',(self.username, self.status))
        elif old_status == self.status:
            return
        else:
            cursor.execute('

    def _get_db(db)
        if db:
            return (db, False)
        else:
            return (self.env.get_db_cnx(), True)
