# Created by Noah Kantrowitz on 2008-04-04.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import types
import copy
from datetime import datetime, timedelta

from trac.core import *
from trac.web.api import IRequestHandler
from trac.ticket.query import Query, QueryModule
from trac.db import get_column_names
from trac.util.datefmt import to_timestamp, utc

from tracforge.admin.api import TracForgeAdminSystem

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
    
    def execute(self, req, db=None, cached_ids=None):
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


class TracForgeQueryModule(QueryModule):
    """A cross-environment query handler."""

    def __init__(self):
        # If you are not coderanger, please don't try to mess with this.
        _old_func = QueryModule.process_request.im_func
        new_globals = copy.copy(_old_func.func_globals)
        new_globals['Query'] = MultiQuery
        self.process_request = types.MethodType(
            types.FunctionType(
                _old_func.func_code,
                new_globals,
                _old_func.func_name,
                _old_func.func_defaults,
                _old_func.func_closure,
            ),
            self,
            type(self),
        )

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/tracforge/query'
    
    # def process_request(self, req):
    # See __init__ for definition

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return ''

    def get_navigation_items(self, req):
        return []
    
    # IContentConverter methods
    def get_supported_conversions(self):
        return []
    
    def convert_content(self, req, mimetype, query, key):
        pass
    
    # IWikiSyntaxProvider methods
    def get_link_resolvers(self):
        return []