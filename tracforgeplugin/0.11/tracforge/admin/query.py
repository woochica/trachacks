# Created by Noah Kantrowitz on 2008-04-04.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.

from datetime import datetime, timedelta

from trac.core import *
from trac.ticket.query import Query, QueryModule
from trac.db import get_column_names
from trac.util.datefmt import to_timestamp, utc

from tracforge.admin.api import TracForgeAdminSystem

class MultiDb(list):
    """Run a query against multiple databases."""
    
    def cursor(self):
        return MultiCursor(self)
    
    def commit(self):
        for db in self:
            db.commit()
    
    def rollback(self):
        for db in self:
            db.rollback()


class MultiCursor(object):
    """Cursor that groks multiple databases."""
    
    def __init__(self, dbs):
        self.cursors = [db.cursor() for db in dbs]
    
    def execute(self, query, args):
        for cursor in self.cursors:
            cursor.execute(query, args)
        self.description = self.cursors[0].description
    
    def __iter__(self):
        for cursor in self.cursors:
            for row in cursor:
                yield row
    
    def fetchall(self):
        buf = []
        for cursor in self.cursors:
            buf += cursor.fetchall()
        return buf


class MultiQuery(Query):
    """A query model object enhanced to handle multiple projects."""
    
    def __init__(self, *args, **kwargs):
        super(MultiQuery, self).__init__(*args, **kwargs)
        self.fields.append({
            'name': 'project',
            'label': 'Project',
            'type': 'select',
            'options': ['tf_client1', 'tf_client2'],
        })
    
    def execute(self, req, cached_ids=None):
        if not self.cols:
            self.get_columns()

        sql, args = self.get_sql(req, cached_ids)
        self.env.log.debug("Query SQL: " + sql % tuple([repr(a) for a in args]))

        results = []
        
        for shortname, env in TracForgeAdminSystem(self.env).get_projects():
            db = env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute(sql, args)
            columns = get_column_names(cursor)
            fields = []
            for column in columns:
                fields += [f for f in self.fields if f['name'] == column] or [None]

            for row in cursor:
                id = int(row[0])
                result = {'id': id, 'href': req.href.ticket(id)}
                for i in range(1, len(columns)):
                    name, field, val = columns[i], fields[i], row[i]
                    if name == self.group:
                        val = val or 'None'
                    elif name == 'reporter':
                        val = val or 'anonymous'
                    elif val is None:
                        val = '--'
                    elif name in ('changetime', 'time'):
                        val = datetime.fromtimestamp(int(val), utc)
                    elif field and field['type'] == 'checkbox':
                        try:
                            val = bool(int(val))
                        except TypeError, ValueError:
                            val = False
                    result[name] = val
                    result['project'] = shortname
                results.append(result)
            cursor.close()
        return results
    

class TracForgeQueryModule(Component):
    """A cross-environment query handler."""
    
    implements()


