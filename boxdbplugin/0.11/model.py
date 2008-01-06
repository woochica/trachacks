# Created by  on 2008-01-02.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.

from boxdb.api import BoxDBSystem

class Document(dict):
    """A single document in the database."""

    def __init__(self, env, name, db=None):
        super(Document, self).__init__()
        self.env = env
        self.name = name
        
        if self.name == 'schema':
            self._bootstrap()
        else:
            data = self._fetch(self.name, db)
            if not data:
                self.type = None
                # Document doesn't exist, return a blank
                return
            
            # Decode the document
            self.type = Document(self.env, data['__type__'][0], db)
            renderers = BoxDBSystem(self.env).renderers_map
            for key, value in data.iteritems():
                key_type = self.type.get(key, 'string')
                if key_type not in renderers:
                    key_type = 'string'
                self[key] = renderers[key_type].decode_property(key, value)

    def _bootstrap(self):
        """Initialize the document that corresponds to the base schema."""
        self.type = self

    def _fetch(self, name, db=None):
        """Retrieve the raw data for a given document."""
        data = {}
        
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        type = self._get_db(cursor, name, '__type__')
        if type:
            # Fetch and decode collection
            type = type[0]
            if type == self.name:
                raise ValueError('Document cannot be its own type')
            
            # Process inheritance
            inherit = self._get_db(cursor, name, '__inherit__')
            if inherit:
                data = self._fetch(inherit[0], db)
            
            local_data = {}
            cursor.execute('SELECT  key, value FROM boxdb WHERE name=%s',
                           (name,))
            for key, value in cursor:
                local_data.setdefault(key, []).append(value)
            
            data.update(local_data)
        return data
    
    def _get_db(self, cursor, name, key):
        """Get an iterable of raw values for a key in this document."""
        cursor.execute('SELECT value FROM boxdb WHERE name=%s AND key=%s',
                       (name, key))
        return [v for v, in cursor]

    def save(self, db=None):
        """Save the changes to the current document."""
        handle_commit = False
        if db is None:
            handle_commit = True
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        # Nuke existing data
        cursor.execute('DELETE FROM boxdb WHERE name=%s', (self.name,))
        
        # Check that we haven't changed schemas
        if self.type is None or self['__type__'] != self.type.name:
            if self['__type__'] == self.name:
                raise ValueError('Document cannot be its own type')
            self.type = Document(self.env, self['__type__'], db)
        renderers = BoxDBSystem(self.env).renderers_map
        
        data = []
        for key, value in self.itervalues():
            key_type = self.type.get(key, 'string')
            if key_type not in renderers:
                key_type = 'string'
            for enc in renderers[key_type].encode_property(key, value):
                data.append((self.name, key, enc))
        cursor.executemany('INSERT INTO boxdb (name, key, value) VALUES (%s, %s, %s)', )
            
    
        