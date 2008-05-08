# Created by Noah Kantrowitz on 2008-04-04.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import types
import copy
from datetime import datetime, timedelta

from trac.core import *
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.web.href import Href
from trac.ticket.api import TicketSystem
from trac.ticket.query import Query, QueryModule
from trac.db import get_column_names
from trac.util.datefmt import to_timestamp, utc
from genshi.filters.transform import Transformer

from tracforge.admin.api import TracForgeAdminSystem

class MultiQuery(Query):
    """A query model object enhanced to handle multiple projects."""
    
    def __init__(self, env, report=None, constraints=None, cols=None,
                 order=None, desc=0, group=None, groupdesc=0, verbose=0,
                 rows=None, page=1, max=Nonee):
        super(MultiQuery, self).__init__(env, report, constraints, cols,
                                         order, desc, group, groupdesc, 
                                         verbose, rows, page, max)
        self.fields.append({
            'name': 'project',
            'label': 'Project',
            'type': 'select',
            'options': [shortname for shortname, env in 
                        TracForgeAdminSystem(self.env).get_projects()],
        })
        field_names = [f['name'] for f in self.fields]
        self.cols = [c for c in cols or [] if c in field_names or 
                     c in ('id', 'time', 'changetime')]
        self.rows = [c for c in rows if c in field_names]
        self.group = group
        if self.group not in field_names:
            self.group = None
    
    def execute(self, req, db=None, cached_ids=None):
        if not self.cols:
            self.get_columns()

        sql, args = self.get_sql(req, cached_ids)
        self.env.log.debug("Query SQL: " + sql % tuple([repr(a) for a in args]))

        results = []
        
        for shortname, env in TracForgeAdminSystem(self.env).get_projects():
            # Check that this project matches the constraints, if any
            if 'project' in self.constraints:
                for con in self.constraints['project']:
                    if con.startswith('!'):
                        test = lambda name: name != con[1:]
                    else:
                        test = lambda name: name == con
                    if test(shortname):
                        break
                else:
                    # No constraints matched, skip this env
                    continue
            
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
                    
                    # Add my new data
                    result['project'] = shortname
                    result['href'] = req.href.projects(shortname, 'ticket', id)
                results.append(result)
            cursor.close()
        return results

    def get_href(self, href, *args, **kwargs):
        href = Href(href.tracforge())
        return super(MultiQuery, self).get_href(href, *args, **kwargs)
    
    def get_sql(self, *args, **kwargs):
        old_constraints = copy.copy(self.constraints)
        old_group = self.group
        old_cols = copy.copy(self.cols)
        if 'project' in self.constraints:
            del self.constraints['project']
        self.group = None
        self.cols.remove('project')
        rv = super(MultiQuery, self).get_sql(*args, **kwargs)
        self.constraints = old_constraints
        self.group = old_group
        self.cols = old_cols
        return rv


class TracForgeQueryModule(QueryModule):
    """A cross-environment query handler."""

    implements(ITemplateStreamFilter)

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
    
    # ITemplateStreamFilter methods
    def match_stream(self, req, method, filename, stream, data):
        return True

    def filter_stream(self, req, method, filename, stream, data):
        if req.path_info == '/tracforge/query':
            stream |= Transformer('//form[@id="query"]').attr('action', req.href.tracforge('query'))
        return stream
    
    # Internal methods
    def _get_constraints(self, req):
        constraints = {}
        ticket_fields = [f['name'] for f in
                         TicketSystem(self.env).get_ticket_fields()]
        ticket_fields.append('id')
        
        # CHANGES FOR TRACFORGE
        ticket_fields.append('project')
        # /CHANGES

        # For clients without JavaScript, we remove constraints here if
        # requested
        remove_constraints = {}
        to_remove = [k[10:] for k in req.args.keys()
                     if k.startswith('rm_filter_')]
        if to_remove: # either empty or containing a single element
            match = re.match(r'(\w+?)_(\d+)$', to_remove[0])
            if match:
                remove_constraints[match.group(1)] = int(match.group(2))
            else:
                remove_constraints[to_remove[0]] = -1

        for field in [k for k in req.args.keys() if k in ticket_fields]:
            vals = req.args[field]
            if not isinstance(vals, (list, tuple)):
                vals = [vals]
            if vals:
                mode = req.args.get(field + '_mode')
                if mode:
                    vals = [mode + x for x in vals]
                if field in remove_constraints:
                    idx = remove_constraints[field]
                    if idx >= 0:
                        del vals[idx]
                        if not vals:
                            continue
                    else:
                        continue
                constraints[field] = vals

        return constraints