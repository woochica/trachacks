from trac.core import *
from trac.web.api import IRequestFilter, IRequestHandler
from trac.perm import IPermissionRequestor
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.report import ReportModule
from trac.util.html import Markup

from ctxtnavadd.api import ICtxtnavAdder
import inspect

import db_default

def _user():
    try:
        for f in inspect.stack():
            if 'req' in f[0].f_locals:
                return f[0].f_locals['req'].args['user']
    finally:
        del f
        
def render_node(log, a_node):
  log('Personal: %s = %s', a_node.name(),a_node.value())

def tree_walk(log, hdf_node):
  while hdf_node: 
    render_node(log, hdf_node)
    tree_walk(log, hdf_node.child())
    hdf_node = hdf_node.next()

class PersonalReportsModule(ReportModule):
    """Allow users to make their own private reports."""
    
    implements(IRequestHandler, IPermissionRequestor, IEnvironmentSetupParticipant, ICtxtnavAdder)
    
    # IRequestHandler methods
    def match_request(self, req):
        if req.path_info.startswith('/preport'):
            path = req.path_info.strip('/').split('/')[1:]
            if len(path) == 1:
                try:
                    int(path[0])
                    req.args['id'] = path[0]
                except ValueError:
                    req.args['user'] = path[0]
            elif len(path) == 2:
                req.args['user'], req.args['id'] = path

            return True
        return False
        
    def process_request(self, req):        
        # Grant permissions if needed
        req.perm.assert_permission('REPORT_PERSONAL')
        if req.args.get('user', req.authname) == req.authname:
            def grant(perm):
                req.perm.perms[perm] = True
                req.hdf['trac.acl.%s'%perm] = '1'
            grant('REPORT_CREATE')
        
        # Silly args hack
        req.args['PREPORTSUSER'] = req.args.get('user', req.authname)
        req.args['PREPORTSCURUSER'] = req.authname
        
        # Hook on redirect
        old_redirect = req.redirect
        def new_redirect(href):
            if href[len(req.href()):].startswith('/report'):
                href = req.href('/p' + href[len(req.href()):].lstrip('/'))
            old_redirect(href)
        req.redirect = new_redirect
        
        rv = super(PersonalReportsModule,self).process_request(req)
        
        # Fix the report hrefs
        if int(req.args.get('id', -1)) == -1:
            hdf_node = req.hdf.getObj('report.items')
            if hdf_node:
                hdf_node = hdf_node.child()
                while hdf_node:
                    report = hdf_node.getValue('report', '-1')
                    href = req.href.preport(report)
                    if 'user' in req.args:
                        href = req.href.preport(req.args['user'], report)
                    req.hdf['report.items.%s.report.report_href'%hdf_node.name()] = href
                    hdf_node = hdf_node.next()
                    
        # Force the 'Available Reports' ctxtnav link to be a link
        req.hdf['chrome.links.up.0.href'] = req.href.report()
        req.hdf['chrome.links.up.0.title'] = 'Available Reports'
        
        # Redirect form submissions
        req.hdf['report.href'] = req.href.preport()
        
        return rv
        
    def get_info(self, db, id, args):
        user = args['PREPORTSUSER']
        if id == -1:
            title = 'Available Reports'
            sql = 'SELECT id AS report, title FROM personal_reports WHERE user = "%s"%sORDER BY report' % \
                (user, user==args['PREPORTSCURUSER'] and ' ' or ' AND private = "0" ')
            description = 'This is a list of reports available for user %s.'%user
            self.log.debug('PersonalReportsModule: %s', sql)
        else:
            cursor = db.cursor()
            cursor.execute('SELECT title, query, description, private FROM personal_reports WHERE user = %s AND id = %s', (user, id))
            row = cursor.fetchone()
            if not row or row[3] == '1' and user != args['PREPORTCURUSER']:
                    raise TracError('Report %d does not exist.' % id,
                                    'Invalid Report Number')
            title = row[0] or ''
            sql = row[1]
            description = row[2] or ''
            
        return [title, description, sql]

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'REPORT_PERSONAL'
        
    # IWikiSyntaxProvider methods
    # NOTE: Need these to prevent the ones from the superclass being duplicated. <NPK>
    def get_link_resolvers(self):
        return []

    def get_wiki_syntax(self):
        return []
        
    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.found_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())
        
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (db_default.name,))
        value = cursor.fetchone()
        if not value:
            self.found_db_version = 0
            return True
        else:
            self.found_db_version = int(value[0])
            #self.log.debug('WeatherWidgetSystem: Found db version %s, current is %s' % (self.found_db_version, db_default.version))
            return self.found_db_version < db_default.version
            
    def upgrade_environment(self, db):
        # 0.10 compatibility hack (thanks Alec)
        try:
            from trac.db import DatabaseManager
            db_manager, _ = DatabaseManager(self.env)._get_connector()
        except ImportError:
                db_manager = db
                
        # Insert the default table
        old_data = {} # {table_name: (col_names, [row, ...]), ...}
        cursor = db.cursor()
        if not self.found_db_version:
            cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",(db_default.name, db_default.version))
        else:
            cursor.execute("UPDATE system SET value=%s WHERE name=%s",(db_default.version, db_default.name))
            for tbl in db_default.tables:
                try:
                    cursor.execute('SELECT * FROM %s'%tbl.name)
                    old_data[tbl.name] = ([d[0] for d in cursor.description], cursor.fetchall())
                    cursor.execute('DROP TABLE %s'%tbl.name)
                except Exception, e:
                    if 'OperationalError' not in e.__class__.__name__:
                        raise e # If it is an OperationalError, just move on to the next table
                            
                
        for tbl in db_default.tables:
            for sql in db_manager.to_sql(tbl):
                cursor.execute(sql)
                    
            # Try to reinsert any old data
            if tbl.name in old_data:
                data = old_data[tbl.name]
                sql = 'INSERT INTO %s (%s) VALUES (%s)' % \
                 (tbl.name, ','.join(data[0]), ','.join(['%s'] * len(data[0])))
                for row in data[1]:
                    try:
                        cursor.execute(sql, row)
                    except Exception, e:
                        if 'OperationalError' not in e.__class__.__name__:
                            raise e
                            
    # ICtxtnavAdder methods
    def match_ctxtnav_add(self, req):
        return req.path_info.startswith('/report') or \
               req.path_info.startswith('/query') or \
               req.path_info.startswith('/preport')
               
    def get_ctxtnav_adds(self, req):
        if req.path_info.startswith('/preport') and 'id' not in req.args:
            yield Markup('Personal Reports')
        else:
            yield req.href.preport(), 'Personal Reports'
            
    # Internal overloads
    def _do_create(self, req, db):
        req.perm.assert_permission('REPORT_CREATE')

        if req.args.has_key('cancel'):
            req.redirect(req.href.preport())

        title = req.args.get('title', '')
        query = req.args.get('query', '')
        description = req.args.get('description', '')
        cursor = db.cursor()
        
        cursor.execute('SELECT max(id) FROM personal_reports WHERE user=%s', (req.authname,))
        row = cursor.fetchone()
        id = row and int(row[0] or 0)+1 or 1
        
        cursor.execute("INSERT INTO personal_reports (id,user,title,query,description) "
                       "VALUES (%s,%s,%s,%s,%s)",(id, req.authname, title, query, description))
        db.commit()
        req.redirect(req.href.preport(id))