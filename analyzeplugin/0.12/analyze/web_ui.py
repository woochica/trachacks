import re
import json
from trac.core import *
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.web.main import IRequestFilter, IRequestHandler
from trac.perm import IPermissionRequestor
from analysis import *

class AnalyzeModule(Component):
    """Base component for analyzing tickets."""
    
    implements(IRequestHandler, ITemplateProvider, IRequestFilter,
               IPermissionRequestor)
    
    analyses = ExtensionPoint(IAnalysis)
    
    # IPermissionRequestor methods  
    def get_permission_actions(self):
        return ['ANALYZE_VIEW']

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('analyze', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if self._valid_request(req):
            add_stylesheet(req, 'analyze/analyze.css')
            add_stylesheet(req, 'analyze/jquery-ui-1.8.16.custom.css')
            add_script(req, 'analyze/jquery-ui-1.8.16.custom.min.js')
            add_script(req, '/analyze/analyze.html')
            add_script(req, 'analyze/analyze.js')
        return template, data, content_type
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/analyze/')
    
    def process_request(self, req):
        data = {'analyses':self._get_analyses(req, check_referer=True),
                'report':get_report(req, check_referer=True)}
        return 'analyze.html', data, 'text/javascript' 
    
    # private methods
    def _valid_request(self, req):
        """Checks permissions and that report can be analyzed."""
        if req.perm.has_permission('ANALYZE_VIEW') and \
          'action=' not in req.query_string and \
          self._get_analyses(req):
            return True
        return False
    
    def _get_analyses(self, req, check_referer=False):
        """Returns a list of analyses for the given report."""
        report = get_report(req, check_referer)
        analyses = []
        for analysis in self.analyses:
            if report and analysis.can_analyze(report):
                analyses.append(analysis)
        return analyses


class AnalyzeAjaxModule(Component):
    """Ajax handler for suggesting solutions to users and fixing issues."""
    implements(IRequestHandler)
    
    analyses = ExtensionPoint(IAnalysis)
    
    # IRequestHandler methods
    def match_request(self, req):
        if req.path_info.startswith('/analyzeajax/'):
            return True

    def process_request(self, req):
        """Process AJAX request."""
        try:
            if req.path_info.endswith('/list'):
                result = self._get_analyses(req.args['report'])
            else:
                for analysis in self.analyses:
                    if not req.path_info.endswith('/'+analysis.path) and  \
                       not req.path_info.endswith('/'+analysis.path+'/fix'):
                        continue
                    db = self.env.get_db_cnx()
                    if req.path_info.endswith('/fix'):
                        result = self._fix_issue(analysis, db, req)
                    else:
                        report = get_report(req, check_referer=True)
                        result = self._get_solutions(analysis, db, req, report)
                    break
                else:
                    raise Exception("Unknown path: %s" % req.path_info)
            code,type,msg = 200,'application/json',json.dumps(result)
        except Exception, e:
            import traceback;
            code,type = 500,'text/plain'
            msg = "Oops...\n"+traceback.format_exc()+"\n"
        req.send_response(code)
        req.send_header('Content-Type', type)
        req.send_header('Content-Length', len(msg))
        req.end_headers()
        req.write(msg)
    
    def _get_analyses(self, report):
        result = []
        for analysis in self.analyses:
            if analysis.can_analyze(report):
                result.append({
                    'path': analysis.path,
                    'num': analysis.num,
                    'title': analysis.title,
                })
        return result
    
    def _get_solutions(self, analysis, db, req, report):
        """Return the solutions with serialized data to use for the fix.
        Ticket references are converted to hrefs."""
        issue,solutions = analysis.get_solutions(db, req.args, report)
        base = req.base_url+'/ticket/'
        id = re.compile(r"(#([1-9][0-9]*))")
        issue = id.sub(r'<a href="%s\2">\1</a>' % base, issue)
        
        # serialize solution data; convert ticket refs to hrefs
        for solution in solutions:
            solution['disabled'] = not req.perm.has_permission('TICKET_MODIFY')
            solution['data'] = json.dumps(solution['data'])
            name = solution['name']
            solution['name'] = id.sub(r'<a href="%s\2">\1</a>' % base, name)
        
        return {'title': analysis.title, 'label': issue,
                'exists': len(solutions) > 0, 'solutions': solutions,
                'refresh': analysis.get_refresh_report() or \
                           get_report(req, check_referer=True)}
    
    def _fix_issue(self, analysis, db, req):
        """Return the result of the fix."""
        data = json.loads(req.args['data'])
        return analysis.fix_issue(db, data, req.authname)


# common functions
def get_report(req, check_referer=False):
    """Returns the report number as a string."""
    report_re = re.compile(r"/report/(?P<num>[1-9][0-9]*)")
    if check_referer:
        path = req.environ.get('HTTP_REFERER','')
    else:
        path = req.path_info
    match = report_re.search(path)
    if match:
        return match.groupdict()['num']
    return None
