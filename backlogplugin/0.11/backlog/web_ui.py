# Backlog plugin

import re

from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider \
                            , add_stylesheet, add_javascript
from trac.ticket.api import ITicketChangeListener
from trac.perm import IPermissionRequestor, PermissionCache, PermissionError

from model import *



from trac.ticket.api import TicketSystem

TicketSystem.get_custom_fields_orig = TicketSystem.get_custom_fields

def _create_ordering_table(db):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT count(*) FROM backlog_ticket")
    except:
        cursor.execute("""
            CREATE TABLE backlog_ticket (bklg_id INTEGER NOT NULL,
              tkt_id INTEGER NOT NULL, tkt_order REAL,
            PRIMARY KEY(bklg_id, tkt_id))""")

def custom_enum_fields(self):    
    fields = self.get_custom_fields_orig()
    config = self.config['ticket-custom']
    
    for field in fields:
        if field['type'] == 'enum':
            field['type'] = 'select'
            name = field['name']
            enum_col = config.get(name + '.options')
            from trac.ticket.model import AbstractEnum
            db = self.env.get_db_cnx()
            enum_cls = type(str(enum_col),(AbstractEnum,), {})
            enum_cls.type = enum_col
            field['options'] = [val.name for val in enum_cls.select(self.env, db=db)]
            
    return fields
    
def get_custom_fields_w_backlog(self):
    fields = self.get_custom_fields_orig()
    config = self.config['ticket-custom']    
    for field in fields:
        if field['type'] == 'backlog':
            field['type'] = 'select'
            name = field['name'] 
            assert name == 'backlog', 'this only works with predefined field name'
            enum_col = config.get(name + '.options')
            field['options'] = [val.name for val in BacklogList(self.env)]
            field['options'].insert(0, NO_BACKLOG)            
    return fields
TicketSystem.get_custom_fields = get_custom_fields_w_backlog 

class BacklogModule(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider\
               , IPermissionRequestor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'backlog'
    
    def get_navigation_items(self, req): 
        if('BACKLOGS_VIEW' in req.perm):       
            yield ('mainnav', 'backlog',
                   tag.a('Backlogs', href=req.href.backlog()))
    
    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/backlog(?:/([0-9]+))?', req.path_info)
        if match:
            if match.group(1):
                req.args['bklg_id'] = match.group(1)
            return True
    
    
    def process_request(self, req):
        req.perm.require('BACKLOGS_VIEW')
        db = self.env.get_db_cnx()
        _create_ordering_table(db)
        bklg_id = req.args.get('bklg_id')
        if bklg_id is None:
            return self._show_backlog_list(req)         
        if req.method == 'POST':
            return self._save_order(req)
        
        return self._show_backlog(req)
    
    def _show_backlog(self, req):
        
        
        self.env.log.info(req.args)

        bklg_id = req.args.get('bklg_id',None)    
        backlog = Backlog(self.env, bklg_id) 
        rw = 'BACKLOG_MODIFY_%s'%backlog.name2perm() in req.perm                                                    
        data = {}
        data['backlog'] = backlog
        data['tickets'], data['tickets2'] = backlog.get_tickets()
        
        for ticket in data['tickets'] + data['tickets2']:
            ticket['sumdesc'] = ticket['summary']
            if(ticket.get('description')): 
                ticket['sumdesc'] += '\n' +  ticket['description']
                if(len(ticket['sumdesc'])) > 250:
                    ticket['sumdesc'] = ticket['sumdesc'][:250] + '...'

        # jquery-ui stylesheet and JS
        add_stylesheet(req, 'backlog/css/jquery-ui-1.7.2.custom.css')
        add_javascript(req, 'backlog/js/jquery-ui-1.7.2.custom.min.js')
        
        #backlog custom stylesheet and JS     
        add_stylesheet(req, 'backlog/css/backlog.css')
        if rw:
            add_javascript(req, 'backlog/js/backlog.rw.js')
        else:
            add_javascript(req, 'backlog/js/backlog.ro.js')

        
        # This tuple is for Genshi (template_name, data, content_type)
        # Without data the trac layout will not appear.
        return 'backlog.html', data, None
    
    def _show_backlog_list(self, req):
        db = self.env.get_db_cnx()
        _create_ordering_table(db)
        bklg_id = req.args.get('bklg_id',None)    
                                                    
        data = {}
                  
        columns = ['id', 'name', 'owner', 'description']

        sql = """SELECT %s, 0 as total, 0 as active
                 FROM  backlog
                 """%(','.join(columns))

        cursor = db.cursor()
        cursor.execute(sql)
        columns.extend(['total', 'active'])
        # creating dictionary with id as key of columnt:value dictionaries
        data['backlogs'] = dict([(backlog[0],(dict(zip(columns, backlog)))) for backlog in cursor]) 

        # get total of tickets in each backlog
        sql = """SELECT bklg_id, count(*) as total
                 FROM backlog_ticket
                 WHERE tkt_order IS NULL OR tkt_order > -1                
                 GROUP BY bklg_id               
              """
        cursor.execute(sql)
        
        for id, total in cursor:
            data['backlogs'][id]['total'] = total            
            data['backlogs'][id]['closed'] = 0
            data['backlogs'][id]['active'] = 0
            
            
        # get total of tickets by status in each backlog
        sql = """SELECT bt.bklg_id, t.status, count(*) as total
                 FROM backlog_ticket bt, ticket t
                 WHERE t.id = bt.tkt_id      
                 AND (bt.tkt_order IS NULL OR bt.tkt_order > -1)        
                 GROUP BY bklg_id, status               
              """
        cursor.execute(sql)    
                
        for id, status, total in cursor:
            print 'status', id, status, total
            if(status == 'closed'):
                data['backlogs'][id]['closed'] += total
            else:
                data['backlogs'][id]['active'] += total
            data['backlogs'][id]['status_%s'%status] = total

        # jquery-ui stylesheet and JS
        add_stylesheet(req, 'backlog/css/jquery-ui-1.7.2.custom.css')
        add_javascript(req, 'backlog/js/jquery-ui-1.7.2.custom.min.js')
        
        #backlog custom stylesheet and JS     
        add_stylesheet(req, 'backlog/css/backlog.css')        
   
        # This tuple is for Genshi (template_name, data, content_type)
        # Without data the trac layout will not appear.
        return 'backlog_list.html', data, None    

    # ITemplateProvider methods
 
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('backlog', resource_filename(__name__, 'htdocs'))]

    def _save_order(self, req):
        bklg_id = req.args.get('bklg_id',0)        
        backlog = Backlog(self.env, bklg_id)
        req.perm.require('BACKLOG_MODIFY_%s'%backlog.name2perm())        
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if(req.args.get('delete_closed','') != ''):
            backlog.remove_closed_tickets()
        if(req.args.get('ticket_order', '') != ''):
            
            ticket_order = req.args.get('ticket_order', '').split(',')
            ticket_order = [int(tkt_id.split('_')[1]) for tkt_id in ticket_order]   
            backlog.set_ticket_order(ticket_order)                        
            #ticket_order = [ (bklg_id, int(tkt_id.split('_')[1]), int(tkt_order)) for (tkt_order, tkt_id) in enumerate(ticket_order)]       
                             
            #print 'ticket_order', ticket_order
            #cursor.executemany('REPLACE INTO backlog_tkt (bklg_id, tkt_id, tkt_order) VALUES (%s, %s, %s)', ticket_order)
        if(req.args.get('tickets_out', '') != ''):
            tickets_out = req.args.get('tickets_out', '').split(',')   
            tickets_out = [ int(tkt_id.split('_')[1]) for tkt_id in tickets_out]     
            backlog.reset_priority(tickets_out)
            print 'tickets_out', tickets_out
            #cursor.executemany('DELETE FROM backlog_ticket WHERE bklg_id=%s AND tkt_id=%s', tickets_out)
        db.commit()
        req.redirect(req.href.backlog(bklg_id))
        return 
      
    # IPermissionRequestor methods

    def get_permission_actions(self):
        backlog = BacklogList(self.env)
        perms = []
        bl_perms = [b.name2perm() for b in bl]        
        modifyandview = ['BACKLOGS_VIEW']    
        modifyandview.extend(['BACKLOG_MODIFY_%s'%bp for bp in bl_perms])      
        owners = [('BACKLOG_OWNER_%s'%bp,['BACKLOGS_VIEW', 'BACKLOG_MODIFY_%s'%bp]) for bp in bl_perms]
        perms.extend(modifyandview)
        perms.extend(owners)        
        perms.append(('BACKLOGS_ADMIN',modifyandview))
        #from pprint import pprint
        #pprint(perms)
        return perms
            
            
            
            
            
        
        

        
