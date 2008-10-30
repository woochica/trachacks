from pkg_resources import resource_filename

from trac.config import Option
from trac.perm import IPermissionRequestor
from trac.core import Component, implements
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.admin.api import IAdminPanelProvider

from trac.util.translation import _

class SQLConstants(Component):
    implements(IAdminPanelProvider, IPermissionRequestor, ITemplateProvider)

    table_name = Option('sql-constants', 'table_name', u"constants", doc="The table that contains constants")

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['SQLCONSTANTS_UPDATE']

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('sqlconstants', resource_filename(__name__, 'htdocs'))]

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'SQLCONSTANTS_UPDATE' in req.perm:
            yield ('database', _('Database'), 'sqlconstants', _('SQL Constants'))

    def get_existing(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT constant, stringval, intval, floatval FROM %s ORDER BY constant' % self.table_name)
        return [dict(name=row[0], stringval=row[1], intval=row[2], floatval=row[3]) for row in cursor]

    def add_new(self, name, value):
        
        stringval = str(value)
        intval = None
        floatval = None
        
        try:
            intval = int(value)
        except:
            intval = 'NULL'
            
        try:
            floatval = float(value)
        except:
            floatval = 'NULL'
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('INSERT INTO %s (constant, stringval, intval, floatval) '
                       'VALUES ("%s", "%s", %s, %s)' % (self.table_name, name, stringval, intval, floatval,))

    def update(self, name, value):
        stringval = str(value)
        intval = None
        floatval = None
        
        try:
            intval = int(value)
        except:
            intval = 'NULL'
            
        try:
            floatval = float(value)
        except:
            floatval = 'NULL'
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('UPDATE %s '
                       'SET stringval="%s", intval=%s, floatval=%s '
                       'WHERE constant="%s"' % (self.table_name, stringval, intval, floatval, name))
                       
    def delete(self, name):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('DELETE FROM %s WHERE constant="%s"' % (self.table_name, name,))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('SQLCONSTANTS_UPDATE')
        
        data = {}
        data['message'] = ""
        data['table_name'] = self.table_name
        
        data['existing'] = existing = self.get_existing()
        
        if req.method == 'POST':
            if 'add_constant' in req.args:
                new_name = req.args['name']
                new_value = req.args['value']
                
                try:
                    self.add_new(new_name, new_value)
                except:
                    data['message'] = "The constant %s already exists or is invalid" % new_name

            elif 'delete_constants' in req.args:
                to_delete = req.args.get('delete', None)
                if to_delete:
                    if isinstance(to_delete, basestring):
                        self.delete(to_delete)
                    else:
                        for name in to_delete:
                            self.delete(name)
            elif 'update_constants' in req.args:
                for c in existing:
                    value = req.args.get('change.%s' % c['name'], None)
                    if value is not None and value != c['stringval']:
                        self.update(c['name'], value)

            data['existing'] = existing = self.get_existing()
        
        add_stylesheet(req, 'sqlconstants/css/sqlconstants.css')
        return 'update.html', data