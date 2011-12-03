import re
from trac.core import *
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.main import IRequestFilter, IRequestHandler
from trac.ticket import TicketSystem, Milestone

class DynamicVariablesModule(Component):
    implements(IRequestHandler, ITemplateProvider, IRequestFilter)
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
#        from pkg_resources import resource_filename
#        return [('dynvars', resource_filename(__name__, 'htdocs'))]
        return []
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        self._validate_request(req, check_referer=True) # redirect if needed
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if self._validate_request(req):
            add_script(req, '/dynvars/dynvars.html')
        return template, data, content_type
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/dynvars/')
    
    def process_request(self, req):
        data = {'vars':{}}
        report = self._get_report(req, check_referer=True)
        for var in self._extract_vars(report):
            data['vars'][var] = self._get_options(var.lower())
        return 'dynvars.html', {'data':data}, 'text/javascript'
    
    # private methods
    def _validate_request(self, req, check_referer=False):
        """Checks permissions and redirects if args are missing."""
        if not req.perm.has_permission('REPORT_VIEW') or \
           'action=' in req.query_string or \
           not self._get_report(req):
            return False
        if check_referer and \
           'action=' in req.environ.get('HTTP_REFERER',''):
            return False
        
        # check for required args, redirect to add if missing
        report = self._get_report(req)
        if not report:
            return False
        vars = self._extract_vars(report)
        if not vars:
            return False
        
        args = []
        for var in vars:
            if var not in req.args:
                options = self._get_options(var.lower())
                if options:
                    val = options[0] or (len(options)>1 and options[1]) or ''
                    args.append('%s=%s' % (var,val))
        if args:
            url = req.base_path + req.path_info + '?' + req.query_string
            if req.query_string:
                url += '&'
            url += '&'.join(args)
            req.redirect(url)
        return True
    
    def _get_report(self, req, check_referer=False):
        """Returns the report number as a string if the request is of
        a report.  The request's path_info is checked first.  If this
        url does not contain the report number and if check_referer is
        True, then the http referer url is checked for the report number."""
        report_re = re.compile(r"/report/(?P<num>[1-9][0-9]*)")
        def extract(url):
            match = report_re.search(url)
            if match:
                return match.groupdict()['num']
            return None
        
        report = extract(req.path_info)
        if report:
            return report
        if check_referer:
            return extract(req.environ.get('HTTP_REFERER',''))
        return None
    
    def _extract_vars(self, report):
        """Return a set of all dynamic variables (if any) found in the
        report.  The special $USER dynamic variable is ignored."""
        args = set([])
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT query FROM report WHERE id=%s", (report,))
        result = cursor.fetchone()
        if result:
            field_re = re.compile(r"\$([A-Z_]+)")
            for arg in field_re.findall(result[0]):
                if arg != 'USER':
                    args.add(arg)
        return args
    
    def _get_options(self, field_name):
        """Return a list of options for the given [dynvars] field:
        
         [dynvars]
         myfield.options = value1|value2|value3
        
        If no [dynvars] field is found, a select field is searched
        and its options returned.  For the milestone field, completed
        milestones are omitted.  If no select field is found, then an
        empty list is returned."""
        # look for [dynvars] field
        for key,val in self.env.config.options('dynvars'):
            if key == field_name+'.options':
                return val.split('|')
        
        # handle milestone special - skip completed milestones
        if field_name == 'milestone':
            return [''] + [m.name for m in
                    Milestone.select(self.env, include_completed=False)]
        
        # lookup select field
        for field in TicketSystem(self.env).get_ticket_fields():
            if field['name'] == field_name and 'options' in field:
                return field['options']
        return []
