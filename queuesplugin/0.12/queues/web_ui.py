import re
import time
import urllib2
from trac.core import *
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.web.main import IRequestFilter, IRequestHandler
from trac.ticket import TicketSystem
from trac.ticket.model import Ticket
from trac.config import ListOption, BoolOption, IntOption, ChoiceOption

class QueuesModule(Component):
    implements(IRequestHandler, ITemplateProvider, IRequestFilter)
    
    reports = ListOption('queues', 'reports', default=[],
            doc="List of report numbers to treat as queues")
    pad_length = IntOption('queues', 'pad_length', default=2,
            doc="Max length of position fields to prefix with 0s")
    max_position = IntOption('queues', 'max_position', default=99,
            doc="Max position value (default is 99); set to 0 for no maximum")
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('queues', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if self._valid_request(req):
            add_stylesheet(req, 'queues/queues.css')
            add_script(req, 'queues/jquery-ui-1.8.16.custom.min.js')
            add_script(req, '/queues/queues.js')
        return template, data, content_type
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/queues/')
    
    def process_request(self, req):
        data = {'groups':self._get_groups(),
                'pad_length':self.pad_length,
                'max_position':self.max_position}
        return 'queues.html', {'data':data}, 'text/javascript' 
    
    # private methods
    def _valid_request(self, req):
        """Checks permissions and that report is a queue report."""
        if req.perm.has_permission('TICKET_MODIFY') and \
          'action=' not in req.query_string and \
          self._get_report(req):
            return True
        return False
    
    def _get_report(self, req):
        """Returns the report number as a string if the request is of
        a queue report listed in the queues config.  For example, only
        urls of reports 11 and 12 would return True for this config but
        any other report url would return False:
        
          [queues]
          reports: 11, 12
        """
        report_re = re.compile(r"/report/(?P<num>[1-9][0-9]*)")
        match = report_re.search(req.path_info)
        if match:
            report = match.groupdict()['num']
            if report in self.reports:
                return report
        return None
    
    def _get_groups(self):
        """Extract from config a mapping of group names to behaviors.
        A sample config file:
        
          [queues]
          group.triage = clear
          group.verifying = ignore
        
        The group names should exactly match the group names in the reports.
        For the above config, a dict is returned with group name as keys
        and the behavior string as the value."""
        groups = {}
        opts = dict(self.env.config.options('queues'))
        for key,val in opts.items():
            if not key.startswith('group.'):
                continue
            groups[key[6:]] = val
        return groups


class QueuesAjaxModule(Component):
    implements(IRequestHandler)
    
    audit = ChoiceOption('queues', 'audit', choices=['log','ticket','none'],
      doc="Record reorderings in log, in ticket, or not at all.")
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/queuesajax')

    def process_request(self, req):
        """Process AJAX request.  Args come back in this form:
        
          id5=position1&id23=position2
        
        where the name is the ticket id prefixed with 'id' and the
        value is the new position value prefixed with the name of
        the first column in the report.
        
        IMPORTANT: DO NOT RENAME THE FIRST COLUMN IN THE REPORT!
        This code assumes that the name of the first column in the
        report exactly matches the ticket's field name.  This is
        to allow any position field name versus hard-coding it.
        """
        try:
            changes = self._get_changes(req.args)
            self._save_changes(changes, req.authname)
            code,msg = 200,"OK"
        except Exception, e:
            import traceback;
            code,msg = 500,"Oops...\n" + traceback.format_exc()+"\n"
        req.send_response(code)
        req.send_header('Content-Type', 'text/plain')
        req.send_header('Content-Length', len(msg))
        req.end_headers()
        req.write(msg);
    
    # private methods
    def _get_changes(self, args):
        """Extract ticket ids and new position values from request args
        that are returned in this form:
        
          id5=position1&id23=position2
        """
        changes = {}
        keyval_re = re.compile(r"(?P<key>[^0-9]+)(?P<val>[0-9]*)")
        for key,val in args.items():
            # get ticket id
            match = keyval_re.search(key)
            if not match:
                continue
            id = match.groupdict()['val']
            if not id:
                continue
            
            # get position field name and value
            match = keyval_re.search(val)
            if not match:
                continue
            field = match.groupdict()['key']
            new_pos = match.groupdict().get('val','')
            
            changes[id] = (field,new_pos)
        return changes
        
    def _save_changes(self, changes, author):
        """Save ticket changes."""
        if self.audit in ('log','none'):
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            for id,(field,new_pos) in changes.items():
                cursor.execute("""
                    SELECT value from ticket_custom
                     WHERE name=%s AND ticket=%s
                    """, (field,id))
                result = cursor.fetchone()
                if result:
                    old_pos = result[0]
                    cursor.execute("""
                        UPDATE ticket_custom SET value=%s
                         WHERE name=%s AND ticket=%s
                        """, (new_pos,field,id))
                else:
                    old_pos = '(none)'
                    cursor.execute("""
                        INSERT INTO ticket_custom (ticket,name,value)
                         VALUES (%s,%s,%s)
                        """, (id,field,new_pos))
                if self.audit == 'log':
                    self.log.info("%s reordered ticket #%s's %s from %s to %s" \
                        % (author,id,field,old_pos,new_pos))
            db.commit()
        else:
            for id,(field,new_pos) in changes.items():
                ticket = Ticket(self.env, id)
                ticket[field] = new_pos
                ticket.save_changes(author=author, comment='')
