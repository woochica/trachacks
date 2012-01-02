import re
import time
import urllib2
from trac.core import *
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.web.main import IRequestFilter, IRequestHandler
from trac.ticket import TicketSystem
from trac.ticket.model import Ticket
from trac.config import ListOption, Option

class VisualizationModule(Component):
    implements(IRequestHandler, ITemplateProvider, IRequestFilter)
    
    SECTION = 'viz'
    DEFAULTS = {
        'source': 'table',
        'query': '',
        'selector': 'table.tickets.listing',
        'type': 'AreaChart',
        'options': 'width:600,height:400',
    }
    
    reports = ListOption(SECTION, 'reports', default=[],
            doc="List of report numbers to treat as queues")
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('viz', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if self._is_valid_request(req):
            add_stylesheet(req, 'viz/viz.css')
            add_script(req, 'viz/viz.js')
            add_script(req, '/viz/viz.html')
        return template, data, content_type
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/viz/')
    
    def process_request(self, req):
        data = self._get_data(req)
        return 'viz.html', data, 'text/javascript' 
    
    # private methods
    def _is_valid_request(self, req):
        """Checks permissions and that page is visualizable."""
        if req.perm.has_permission('TICKET_VIEW') and \
          'action=' not in req.query_string and \
          self._get_section(req):
            return True
        return False
    
    def _get_section(self, req, check_referer=False):
        """Returns the trac.ini section that best matches the page url.
        There's a default section [viz] plus regex defined sections:
        
          [viz]
          reports = 11,12
          options = width:400,height:300
          
          [viz.report/12]
          options = colors:['red','orange']
          
          [viz.milestone]
          type = ColumnChart
          options = isStacked:true
        
        In this example, here are results for different page urls:
        
          /report/1      ->  None
          /report/11     ->  'viz'
          /report/12     ->  'viz.report/12'
          /milestone/m1  ->  'viz.milestone'
        """
        if check_referer:
            path = req.environ.get('HTTP_REFERER','')
        else:
            path = req.path_info
        
        # check regex sections
        for section in self.env.config.sections():
            if not section.startswith('%s.' % self.SECTION):
                continue
            section_re = re.compile(section[len(self.SECTION)+1:])
            if section_re.search(path):
                return section
        
        # check reports list
        report_re = re.compile(r"/report/(?P<num>[1-9][0-9]*)")
        match = report_re.search(req.path_info)
        if match:
            report = match.groupdict()['num']
            if report in self.reports:
                return self.SECTION
        
        return None
    
    def _get_data(self, req):
        """Return the template data for the given request url."""
        data = {}
        section = self._get_section(req, check_referer=True)
        
        # override [viz] with regex section
        for key,default in self.DEFAULTS.items():
            data[key] = self.env.config.get(self.SECTION,key,default) # [viz]
            if section != self.SECTION:
                data[key] = self.env.config.get(section,key,data[key])
        
        # redo options - make additive
        key,default = 'options',self.DEFAULTS['options']
        data[key] = self.env.config.get(self.SECTION,key,default) # [viz]
        if section != self.SECTION:
            options = self.env.config.get(section,key,data[key])
            if data[key] != options:
                data[key] = (data[key] + ',' + options).strip(',')
        
        return data
