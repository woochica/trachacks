"""
Extented Mail Plugin

XMail provides extensive user specific mail options, including cycled mail deliveries.

Basically there are two different kind of filtered mail delivery:
 1. cycled mails (e.g. daily, weekly, etc.)
 1. immediate mail, but with a user-specific filter (e.g. only high-prio tickets)
"""

import re
import pkg_resources

from genshi.builder import tag
from genshi.filters import Transformer

from trac.core import Component, implements
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet,\
    add_script

from trac.util.translation import domain_functions
from xmail.XMailFilterObject import FilterObject, XMAIL_TABLE, create_table,\
    get_col_list
from xmail.XMailEMailModule import XMailEventHandler
from trac.util import datefmt
from trac.util.datefmt import get_date_format_hint, get_datetime_format_hint,to_datetime,format_datetime
from trac.ticket.api import TicketSystem
import XMailPermissions

#from trac.db.api import DatabaseManager


# i18n support for plugins, available since Trac r7705 
# use _, tag_ and N_ as usual, e.g. _("this is a message text") 
_, tag_, N_, add_domain = domain_functions('xmail',  '_', 'tag_', 'N_', 'add_domain')

INTERVAL_LIST = {0: _('immediately'), 86400: _('daily'), 604800: _('weekly')}

#===============================================================================
# 
# TODO[fm]: implement also IEnvironmentSetupParticipant, since there could be checked,
# if this plugin needs an upgrade
#===============================================================================
class XMailMainView(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)
    
    # path to xmail view
    MY_PATH = 'xmail'
    _CONFIG_SECTION = 'xmail-plugin'
    
    
    def __init__(self):
        self._version = None 
        self.ui = None 
        # bind the 'traccsubtickets' catalog to the locale directory 
        locale_dir = pkg_resources.resource_filename(__name__, 'locale') 
        add_domain(self.env.path, locale_dir)
         
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if XMailPermissions.checkPermissions(self,req):
            return self.MY_PATH
    
    def get_navigation_items(self, req):
        if XMailPermissions.checkPermissions(self,req):
            yield ('mainnav', self.MY_PATH,
                   tag.a('XMail', href=req.href.xmail()))
        
    # IRequestHandler methods
    def match_request(self, req):
        if XMailPermissions.checkPermissions(self,req):
            return re.match(r'/' + self.MY_PATH + '(?:_trac)?(?:/.*)?$', req.path_info)
    
    def process_request(self, req):
        if XMailPermissions.checkPermissions(self,req):
            if ( req.path_info == "/xmail" ):
                if self._check_init() == False:
                    create_table(self.env)
                    self.log.info("table successfully initialized")
                       
                #deleting one filter
                act = None
                try: 
                    if req.args.has_key('xmailAction') and req.args.has_key('action_sel'):
                        action_sel = req.args['action_sel']
                        act = req.args['xmailAction']
                        if not act or not action_sel:
                            pass
                        elif act == 'delete':
                            self._deleteFilter(action_sel)
                        elif act == 'activate':
                            self._update_filter(action_sel, 'active', 1)
                        elif act == 'deactivate':
                            self._update_filter(action_sel, 'active', None)
                except Exception, e: #pass
                    self.log.error( "[process_request] error while executing action %s occured: %s" % (act, e) )
                
                return self.print_main_view(req)
            
            elif ( re.match(r'/' + self.MY_PATH + '/xmail-edit.html(?:id.*)?$', req.path_info) ):
                # edit filter
                filter = self._getFilterObject(req)
                id = None
                save = None
                try: 
                    id = req.args['id']
                    save = req.args['Save']
                except: pass
                if id and not save:
                    filter.load_filter(self.env.get_db_cnx(), id)
                    return self.print_edit_view(req, filter=filter)
                elif id and filter.check_filter(): 
                    #update existing data
                    try:
                        filter.save(self.env.get_db_cnx(), True, id)
                        return self.print_main_view(req)
                    except Exception, e:
                        self.xmaillog("DEBUG:XMailMainView.process_request: Exception risen by filter.save(self.env.get_db_cnx(), True, id)\n\t%s" % e.args[1])
                        self.xmaillog("DEBUG:XMailMainView.process_request: sql_Statement was:\n%s" % str(e.args[0]))
                        self.log.error( "[process_request] error while executing save occured: %s" % (e.args[1]) )
                        return self.print_edit_view(req, e, filter=filter)
                elif filter.check_filter():
                    try:
                        filter.save(self.env.get_db_cnx())
                        return self.print_main_view(req)
                    except Exception, e:
                        #warning
                        if type(e)==Warning:
                            w = Warning("Illegal value for field 'whereClause'.",e)
                            return self.print_edit_view(req, filter=filter,warning=w)
                        else:
                            e = Exception("Warning occurred until saving Data",e)
                            return self.print_edit_view(req, filter=filter,error=e)
                    except Warning, w:
                        print "warning"
                        
                elif req.environ.get('REQUEST_METHOD') == 'POST':
                    w = Warning("Fields not set","Empty fields: %s"%', '.join(filter.getEmptyFields()))
                    return self.print_edit_view(req,None,filter=filter,warning=w)
                else:
                    return self.print_edit_view(req, filter=filter)
            elif ( re.match(r'/' + self.MY_PATH + '/xmail-listresults.html(?:id.*)?$', req.path_info) ):
                return self.print_list_view(req)
            else:
                self.log.error( "request path unknown: " + req.path_info )
                raise Exception("request path unknown: " + req.path_info)
 
 
    #=======================================================================
    # Returing a FilterObject (singelton)
    #=======================================================================
    def _getFilterObject(self,req):
        return FilterObject(req)
          
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]
    
#    ******************************
#    internal methods
#    ******************************
    
    def _check_init(self):
        """First setup or initentities deleted
            check initialization, like db setup etc.
            copied from DbModul.py of ticketbudgeting-plugin
        """
        if ( self.config.get(self._CONFIG_SECTION, 'name') ):
            self.log.debug ( "have local ini, so everything is set" )
            return True
        else:
            self.log.debug ( "check database" )
            sql = "select id from xmail;"
            db = self.env.get_db_cnx()
            myCursor = db.cursor()
            try:
                myCursor.execute(sql)
                self.config.set(self._CONFIG_SECTION, 'name', 'xmail')
                self.log.debug ( "created local ini entries with name xmail" )
                return True
            except Exception:
                self.log.warn ( "[_check_init] error while checking database; table 'xmail' is probably not present" )
            db.close()

        return False
    
    #===========================================================================
    # print methods
    #===========================================================================
    def print_main_view(self, req):
        filter = self._getFilterObject(req)
        userMail = self.get_user_email(filter.username)

        if not userMail:
            userMail = ["No email specified"]
            
#        header_names = [_('id'), _('filter name'), _('next execution'), _('last successful execution'),
#                        _('interval in sec'), _('actions')]

        sql = "select " + get_col_list(['username', 'selectfields', 'whereclause'])
        sql += " from " + XMAIL_TABLE.name + " where username='" + req.authname + "' order by filtername"
        self.log.debug( "print_main_view -- sql: %s" % sql )
        rows, col_list = self.get_data(sql)
        col_list.append('actions')
        
        data = {'userEmail' : userMail[0], 
                'table_headers': col_list,
                'sql_result': rows,
                'filter': filter,
                'list_interval': INTERVAL_LIST}
        
        add_stylesheet(req, 'hw/css/style.css')
        add_script(req, 'hw/js/xmail.js')
        
        return 'xmail-mainview.html', data, None
    
    def print_list_view(self, req):
        #req = self.buildSqlParts(req)
        id = req.args['id']
        filter = self._getFilterObject(req)

        try:
            db = self.env.get_db_cnx()
            filter.load_filter(db, id)
            sql = filter.get_filter_select_from_db(db, id)
            sql_result, table_headers = filter.get_result(db, sql)
            data = {'id': id, 'sql': sql,
                    'filter_name': filter.values['filtername'],
                    'table_headers': table_headers,
                    'sql_result': sql_result}
        except Exception, e:
            try:
                sql, ex = e
                data = {'id': id, 'sql': sql, 
                        'error': ex }
            except:
                self.log.error( "Severe exception: " + str(e) )
                
        add_stylesheet(req, 'hw/css/style.css')
        return 'xmail-listresults.html', data, None
    
    def print_edit_view(self, req, error=None, filter=None, warning=None):

        userMail = self.get_user_email(req.authname)
        fields = TicketSystem(self.env).get_ticket_fields()
        customFields = TicketSystem(self.env).get_custom_fields()

        for  f in fields[:]:
            for cf in customFields:
                if f['name'] == cf['name']:
                    fields.remove(f)

        disableSubmitButton = ""
        if not userMail:
            userMail = ["No email specified"]
            disableSubmitButton = "disabled"

        data = {'userEmail' : userMail, 
                'submitDisabled': disableSubmitButton,
                'datetime_hint': get_datetime_format_hint(),
                'fields': fields,
                'filter': filter,
                'error': error,
                'warning': warning}
        
        add_stylesheet(req, 'hw/css/style.css')
        add_script(req, 'hw/js/xmail.js')
        
        return 'xmail-edit.html', data, None
         
    #===========================================================================
    # data methods
    #===========================================================================
    
    def _deleteFilter(self, action_sel):
        """delete list of filters"""
        
        if not action_sel or len(action_sel) == 0:
            return
        
        id_list = None
        for id in action_sel:
            if id and id > 0:
                if id_list == None:
                    id_list = "%s" % id
                else:
                    id_list += ",%s" % id
                
        if id_list:
            self.execute_sql_query('delete from %s where id in(%s)'%(XMAIL_TABLE.name,id_list))
            self.log.debug( 'deleted %s filter(s) -- ids: %s' % (len(action_sel), id_list) )
    
    def _update_filter(self, action_sel, action=None, value=None):
        if not action_sel or len(action_sel) == 0 \
            or not action:
            return
        
        if not value:
            value = 'null'
        
        id_list = None
        for id in action_sel:
            if id and id > 0:
                if id_list == None:
                    id_list = "%s" % id
                else:
                    id_list += ",%s" % id
                    
        if id_list:
            self.execute_sql_query('update %s set %s = %s where id in (%s)' %
                                   (XMAIL_TABLE.name, action, value, id_list) )
            self.log.debug( 'updated %s filter(s) -- ids: %s' % (len(action_sel), id_list) )            
    
    def get_data(self, sql):
        db = self.env.get_db_cnx()
        myCursor = db.cursor()
        data = []
        col_list = []
        try:
            myCursor.execute(sql)
            cols = myCursor.description
            for col in cols:
                col_list.append(col[0])
                
            for row in myCursor:
                newRow = {}
#                row = list(myCursor.fetchone())
                for i, col in enumerate(col_list):
                    newRow[col] = row[i]
                data.append(newRow)
#            data = list(myCursor.fetchall())
            
            db.commit()
        except Exception, e:
            self.log.error ( "[print_mail_list] SQL:\n %s \n produced exception: %s" % (sql,e))
            
        db.close()
        return data, col_list
    
    """
        gets user email address
    """
    def get_user_email(self, username):
        db = self.env.get_db_cnx()
        myCursor = db.cursor()
        sql = "select value from session_attribute where sid='" + username + "' and name='email'"
        sqlResult = None
        
        try:
            myCursor.execute(sql)
            sqlResult = list(myCursor.fetchall())
            db.commit()
        except Exception, e:
            self.log.error ( "Error executing SQL Statement \n ( %s ) \n %s" % (sql, e))
            db.rollback()
        
        if sqlResult and ( len(sqlResult) == 1 ):
            return sqlResult[0]
        else:
            return None
        
    def get_report_list(self, username):
        db = self.env.get_db_cnx()
        myCursor = db.cursor()
        sql = "select value from session_attribute where sid='" + username + "' and name='email'"
        sqlResult = None
        
        try:
            myCursor.execute(sql)
            sqlResult = list(myCursor.fetchall())
            db.commit()
        except Exception, e:
            self.log.error ( "Error executing SQL Statement \n ( %s ) \n %s" % (sql, e))
            db.rollback()
        db.close()
        
        if sqlResult and ( len(sqlResult) == 1 ):
            return sqlResult[0]
        else:
            return None
        
    def execute_sql_query(self, sqlQuery, *params):
        db = self.env.get_db_cnx()
        myCursor = db.cursor()
        sucess = False
        try:
            myCursor.execute(sqlQuery, params)
            db.commit()
            sucess = True
        except Exception, e:
            self.log.error ( "Error executing SQL Statement \n ( %s ) \n %s" % (sqlQuery,e))
            db.rollback()
        db.close()
            
        return sucess
    
    def xmaillog (self, message):
        f = open('/opt/trac/projects/Legato/log/xmailplugin.log', 'r+')
        f.seek(0,2)
        f.write('%s\n' % message)
        f.close()