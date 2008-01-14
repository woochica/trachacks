# Created by  on 2008-01-02.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
from datetime import datetime

from trac.util.datefmt import to_timestamp, utc
from trac.util.compat import set

from boxdb.api import BoxDBSystem
from boxdb.compat import simplejson

class Document(dict):
    """A single document in the database."""

    def __init__(self, env, name, db=None):
        super(Document, self).__init__()
        self.env = env
        self.name = name
        self._old_data = {}
        
        if self.name == 'schema':
            self._bootstrap()
        else:
            self._fetch(self.name, db)
            if not self:
                self.type = None
                # Document doesn't exist, return a blank
                return
            
            self._old_data.update(self)
            
            # Decode the document
            self.type = Document(self.env, self.type, db)
            for key, value in self.iteritems():
                self[key] = simplejson.loads(value)

    def _bootstrap(self):
        """Initialize the document that corresponds to the base schema."""
        self.type = self

    def _fetch(self, name, db=None):
        """Retrieve the raw data for a given document."""
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        type = self._get_db(cursor, name, '__type__')
        if type:
            # Fetch and decode collection
            type = simplejson.loads(type)
            if type == self.name:
                raise ValueError('Document cannot be its own type')
            self.type = type
            
            # Process inheritance
            inherit = self._get_db(cursor, name, '__inherit__')
            if inherit:
                inherit = simplejson.loads(inherit)
                self._fetch(inherit, db)
            
            cursor.execute('SELECT  key, value FROM boxdb WHERE name=%s',
                           (name,))
            for key, value in cursor:
                self[key] = value

    def _get_db(self, cursor, name, key):
        """Get an iterable of raw values for a key in this document."""
        cursor.execute('SELECT value FROM boxdb WHERE name=%s AND key=%s',
                       (name, key))
        val = cursor.fetchone()
        if val is None:
            return val
        else:
            return val[0]

    def save(self, db=None):
        """Save the changes to the current document."""
        author = 'coderanger'
        when = None
        comment = 'This is a comment'
        
        if when is None:
            when = datetime.now(utc)
        when_ts = to_timestamp(when)
        
        handle_commit = False
        if db is None:
            handle_commit = True
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        data = dict([(key, simplejson.dumps(value)) for key, value in self.iteritems()])
        
        sql_queue = [('__comment__', simplejson.dumps(comment), '')]
        for key in set(data.iterkeys()) | set(self._old_data.iterkeys()):
            if key not in data:
                # Key deleted
                cursor.execute('DELETE FROM boxdb WHERE name=%s AND key=%s',
                               (self.name, key))
                sql_queue.append((key, self._old_data[key], ''))
            elif key not in self._old_data:
                # Key added
                cursor.execute('INSERT INTO boxdb (name, key, value) VALUES (%s, %s, %s)',
                               (self.name, key, data[key]))
                sql_queue.append((key, '', data[key]))
            elif data[key] != self._old_data[key]:
                # Key changed
                cursor.execute('UPDATE boxdb SET value=%s WHERE name=%s AND key=%s',
                               (data[key], self.name, key))
                sql_queue.append((key, self._old_data[key], data[key]))
        
        for key, old, new in sql_queue:
            cursor.execute('INSERT INTO boxdb_changes (document, time, author, key, oldvalue, newvalue) VALUES (%s, %s, %s, %s, %s, %s)',
                           (self.name, when_ts, author, key, old, new))
        
        if handle_commit:
            db.commit()

    def get_changelog(self, when=None, db=None):
        """Return a iterable of the form:
        (time, author, key, oldvalue, newvalue)
        """
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        when_ts = when and to_timestamp(when) or 0
        if when_ts:
            cursor.execute('SELECT time, author, key, oldvalue, newvalue '
                           'FROM boxdb_changes '
                           'WHERE document=%s AND time=%s'
                           'ORDER BY time',
                           (self.name, when_ts))
        else:
            cursor.execute('SELECT time, author, key, oldvalue, newvalue '
                           'FROM boxdb_changes '
                           'WHERE document=%s'
                           'ORDER BY time',
                           (self.name,))
        for t, author, key, oldvalue, newvalue in cursor:
            t = datetime.fromtimestamp(int(t), utc)
            
            if oldvalue:
                oldvalue = simplejson.loads(oldvalue)
            else:
                oldvalue = None
            
            if newvalue:
                newvalue = simplejson.loads(newvalue)
            else:
                newvalue = None
            
            yield t, author, key, oldvalue, newvalue